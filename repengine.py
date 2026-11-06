# -*- coding: utf-8 -*-
"""موتور گزارش‌سازی — ساخت کوئری امن از مشخصات گزارش، اتصال خودکار جدول‌های والد،
ترجمه مقادیر، گروه‌بندی/تجمیع و خروجی CSV/Excel.

امنیت: نام جدول/ستون فقط از متادیتای مجاز انتخاب می‌شود و مقادیر پارامتری بایند
می‌شوند؛ هیچ رشته‌ای از کاربر مستقیماً داخل SQL قرار نمی‌گیرد.
"""

import csv
import io
import json
import re
import time
import zipfile

import catalog as C
import dbkit as D
import jalali as J

MAX_DISPLAY_ROWS = 5000
DEFAULT_DISPLAY_ROWS = 200
MAX_EXPORT_ROWS = 100000

OPS = {
    'eq': '=', 'ne': '!=', 'gt': '>', 'ge': '>=', 'lt': '<', 'le': '<=',
    'contains': 'LIKE', 'ncontains': 'NOT LIKE',
    'empty': 'IS NULL', 'notempty': 'IS NOT NULL', 'in': 'IN',
}


# ---------------- ابزارهای ستون ----------------

IDNUM_COLS = {'NID', 'Mobile', 'Mobile2', 'RefID', 'UserNID', 'ZipCode', 'PostalCode',
              'ApplicantNID', 'ConsultantNID', 'SecretaryNID', 'APICode', 'HadPaymentRefID',
              'TrackingCode', 'Number', 'DetailCode', 'HaiatID', 'GroupID',
              'InstituteUniqueID', 'SmsReceiver'}

# ستون‌های مبلغ/وزن که در MySQL نوع DECIMAL دارند ولی در SQLite TEXT ذخیره می‌شوند
DEC_COLS = {'Amount', 'Fee', 'TaxAmount', 'TotalPayment', 'UserTariff', 'AcceptorFee',
            'SecretaryFee', 'SupervisorFee', 'CenterFee', 'AdminFee', 'Remained',
            'Reserved', 'Used', 'Assigned', 'AmountBefore', 'HadPaymentAmount',
            'Weight', 'Discount', 'Percent'}


def col_kind(meta, table, col):
    """نوع منطقی ستون: int/text/date/decimal/bit/idnum"""
    if _is_date_col(table, col):
        return 'date'
    t = (D.col_type(meta, table, col) or 'TEXT').upper()
    if col in IDNUM_COLS:
        return 'idnum'
    if col in DEC_COLS:
        return 'decimal'
    if 'DECIMAL' in t or 'REAL' in t or 'FLOAT' in t or 'DOUBLE' in t:
        return 'decimal'
    if 'INT' in t or t == 'BIT':
        return 'int'
    return 'text'


def _is_date_col(table, col):
    return col in (C.DATES.get(table) or [])


def label_expr(fkdef, alias):
    """عبارت نمایش والد برای FK — نام و نام خانوادگی یا عنوان"""
    cols = fkdef.get('label') or ['id']
    if len(cols) == 1:
        return f'NULLIF({alias}."{cols[0]}", \'\')'
    return (f"NULLIF(TRIM(COALESCE({alias}.\"{cols[0]}\",'') || ' ' || "
            f"COALESCE({alias}.\"{cols[1]}\",'')), '')")


# ---------------- ساخت کوئری عمومی جدول ----------------

def build_table_query(meta, table, spec):
    """کوئری گزارش عمومی یک جدول را می‌سازد.

    خروجی: (sql, params, out_cols, joins_info, error)
      out_cols = [{key, label, kind, dict, fk, date}]
    """
    info = meta.get(table)
    if not info or info['kind'] != 'table':
        return None, None, None, None, f'جدول «{table}» یافت نشد.'
    all_cols = info['cols']
    if not all_cols:
        # ستون‌ها را از خود جدول بخوان
        try:
            all_cols = [r[1] for r in conn_pragma(meta, info['sname'])]
        except Exception:
            all_cols = []
    if not all_cols:
        return None, None, None, None, f'ستون‌های «{table}» در دسترس نیست.'

    want = spec.get('columns') or []
    cols = [c for c in want if c in all_cols] if want else list(all_cols)
    cols = [c for c in cols if not C.is_sensitive(table, c)]
    if not cols:
        return None, None, None, None, 'هیچ ستون معتبری انتخاب نشده است.'

    sn = info['sname']
    params = []
    selects, joins, out_cols = [], [], []
    used_alias = set()

    for i, col in enumerate(cols):
        a = f't{table}'
        sel = f'{a}."{col}"'
        fkdef = C.FK.get(f'{table}.{col}')
        dkey = C.dict_key(table, col)
        kind = col_kind(meta, table, col)
        # ستون‌های ServiceID → دیکشنری خدمات (سها برای جدول‌های ارجاع)
        if dkey is None and col in ('ServiceID',) and fkdef:
            dkey = 'service'
            via = (fkdef.get('via') or 'id')
        elif isinstance(dkey, str):
            via = None
        else:
            via = None
        oc = {'key': col, 'label': C.col_label(table, col), 'kind': kind,
              'dict': dkey if isinstance(dkey, (dict, str)) else None,
              'via': via if dkey == 'service' else None,
              'fk': bool(fkdef), 'date': _is_date_col(table, col)}
        if fkdef:
            parent = fkdef['parent']
            pinfo = meta.get(parent)
            if pinfo:
                alias = f'j{i}_{pinfo["sname"]}'
                if alias not in used_alias:
                    used_alias.add(alias)
                    pcol = 'NID' if fkdef.get('by') == 'nid' else _pk_of(pinfo)
                    joins.append(f'LEFT JOIN "{pinfo["sname"]}" AS {alias} '
                                 f'ON {a}."{col}" = {alias}."{pcol}"')
                    sel = f'{label_expr(fkdef, alias)}'
                    oc['label'] += ' (نام)'
                    oc['fk_label_of'] = col
                    # برچسب اول، مقدار خام بعد (برای فیلتر/ارجاع — در خروجی پنهان)
                    selects.append(sel)
                    out_cols.append(oc)
                    selects.append(f'{a}."{col}"')
                    out_cols.append({'key': col, 'label': '—', 'hidden': True,
                                     'kind': kind})
                    continue
        selects.append(sel)
        out_cols.append(oc)

    where, params = build_where(meta, table, spec, all_cols)

    group = spec.get('group_by') or []
    aggs = spec.get('aggs') or []
    if group:
        return build_group_query(meta, table, sn, group, aggs, where, params,
                                 spec, all_cols)

    order = spec.get('order') or []
    order_sql = ''
    if order:
        parts = []
        for o in order[:2]:
            col = o.get('col')
            direction = 'DESC' if (o.get('dir') or 'desc').lower() == 'desc' else 'ASC'
            if col in cols and not C.is_sensitive(table, col):
                # جایگاه ستون در SELECT (شماره ترتیبی) از روی out_cols
                for oi, occ in enumerate(out_cols):
                    if occ.get('key') == col and not occ.get('hidden'):
                        parts.append(f'{oi + 1} {direction}')
                        break
        if parts:
            order_sql = 'ORDER BY ' + ', '.join(parts)

    limit = int(spec.get('limit') or DEFAULT_DISPLAY_ROWS)
    limit = max(1, min(limit, MAX_DISPLAY_ROWS))
    offset = max(0, int(spec.get('offset') or 0))

    sql = (f'SELECT {", ".join(selects)} FROM "{sn}" AS t{table} '
           f'{" ".join(joins)} '
           f'WHERE {where} {order_sql} LIMIT {limit} OFFSET {offset}')
    return sql, params, out_cols, None, None


def conn_pragma(meta, sname_):
    # برای جدول‌های بدون متادیتا
    conn, _ = D.connect()
    try:
        return conn.execute(f'PRAGMA table_info("{sname_}")').fetchall()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _pk_of(pinfo):
    cols = pinfo['cols']
    if 'id' in cols:
        return 'id'
    if 'Id' in cols:
        return 'Id'
    return cols[0] if cols else 'id'


def build_where(meta, table, spec, all_cols):
    """ساخت WHERE از فیلترهای مشخصات + جستجوی سراسری + بازه تاریخ سریع"""
    sn = (meta.get(table) or {}).get('sname', table)
    clauses, params = [], []
    for f in spec.get('filters') or []:
        col = f.get('col')
        if col not in all_cols or C.is_sensitive(table, col):
            continue
        opname = f.get('op') or 'eq'          # نام نمادین: eq/contains/...
        op = OPS.get(opname, '=')             # عملگر SQL: '=' / 'LIKE' / ...
        val = f.get('value')
        kind = col_kind(meta, table, col)
        # تاریخ شمسی → میلادی
        if kind == 'date' and isinstance(val, str) and val.strip() \
                and opname in ('eq', 'ne', 'gt', 'ge', 'lt', 'le'):
            iso = J.jalali_to_iso(val, end_of_day=(opname in ('le', 'lt')))
            if iso:
                val = iso
        fkdef = C.FK.get(f'{table}.{col}')
        target = f't{table}."{col}"'
        # فیلتر متنی روی نام والد برای ستون‌های FK
        if fkdef and isinstance(val, str) and not re.match(r'^-?\d+$', val.strip() or 'x') \
                and opname in ('eq', 'contains'):
            pinfo = meta.get(fkdef['parent'])
            if pinfo:
                pcol = 'NID' if fkdef.get('by') == 'nid' else _pk_of(pinfo)
                clauses.append(
                    f't{table}."{col}" IN (SELECT x."{pcol}" FROM "{pinfo["sname"]}" AS x '
                    f'WHERE x."{(fkdef.get("label") or ["id"])[0]}" LIKE ?)')
                params.append(f'%{val.strip()}%')
                continue
        if opname in ('empty', 'notempty'):
            clauses.append(f'{target} ' + ('IS NULL' if opname == 'empty' else 'IS NOT NULL'))
        elif opname in ('eq', 'ne', 'gt', 'ge', 'lt', 'le'):
            if val in (None, ''):
                continue
            clauses.append(f'{target} {op} ?')
            params.append(_cast(kind, val))
        elif opname == 'contains':
            if val in (None, ''):
                continue
            # فیلتر ستونی تاریخ شمسی: «1404» / «1404/07» / «1404/07/12» → بازه ISO
            if kind == 'date':
                rng = _jdate_prefix(str(val).strip())
                if rng:
                    clauses.append(f'{target} BETWEEN ? AND ?')
                    params.extend(rng)
                    continue
            clauses.append(f'{target} LIKE ?')
            params.append(f'%{val}%')
        elif opname == 'ncontains':
            if val in (None, ''):
                continue
            clauses.append(f'{target} NOT LIKE ?')
            params.append(f'%{val}%')
        elif opname == 'in':
            vals = [v for v in re.split(r'[,\n]', str(val or '')) if v.strip()]
            if not vals:
                continue
            qs = ','.join('?' * len(vals))
            clauses.append(f'{target} IN ({qs})')
            params.extend(_cast(kind, v) for v in vals)

    # بازه تاریخ سریع روی ستون تاریخ اصلی
    pdate = C.PRIMARY_DATE.get(table)
    if pdate and pdate in all_cols:
        df = J.jalali_to_iso(spec.get('date_from') or '')
        dt = J.jalali_to_iso(spec.get('date_to') or '', end_of_day=True)
        if df:
            clauses.append(f't{table}."{pdate}" >= ?')
            params.append(df)
        if dt:
            clauses.append(f't{table}."{pdate}" <= ?')
            params.append(dt)

    # جستجوی سراسری
    q = (spec.get('search') or '').strip()
    if q:
        qparts = []
        text_cols = [c for c in all_cols[:10] if not C.is_sensitive(table, c)]
        for c in text_cols:
            kind = col_kind(meta, table, c)
            if kind in ('text', 'idnum'):
                qparts.append(f't{table}."{c}" LIKE ?')
                params.append(f'%{q}%')
        if qparts:
            clauses.append('(' + ' OR '.join(qparts) + ')')

    return (' AND '.join(clauses) if clauses else '1=1'), params


def _cast(kind, val):
    s = str(val).strip()
    if kind == 'int':
        try:
            return int(float(s))
        except ValueError:
            return val
    if kind == 'decimal':
        try:
            return float(s)
        except ValueError:
            return val
    if kind in ('date',):
        iso = J.jalali_to_iso(s, end_of_day=True) or s
        return iso
    return val


_J_YM_RE = re.compile(r'^(\d{4})\s*[/\-.]\s*(\d{1,2})$')
_J_Y_RE = re.compile(r'^(\d{4})$')


def _jdate_prefix(text):
    """تاریخ شمسی جزئی → بازه ISO (شروع، پایان) برای فیلتر «شامل»:
    1404/07/12 → آن روز | 1404/07 → کل ماه | 1404 → کل سال"""
    s = text.strip()
    if not s:
        return None
    iso = J.jalali_to_iso(s)
    if iso:
        return (iso, iso + ' 23:59:59')
    m = _J_YM_RE.match(s)
    if m:
        jy, jm = int(m.group(1)), int(m.group(2))
        try:
            gy, gm, gd = J.to_gregorian(jy, jm, 1)
            end_iso = _jmonth_end_iso(jy, jm)
            if end_iso:
                return (f'{gy:04d}-{gm:02d}-{gd:02d}', end_iso + ' 23:59:59')
        except Exception:
            return None
        return None
    m = _J_Y_RE.match(s)
    if m:
        jy = int(m.group(1))
        try:
            gy, gm, gd = J.to_gregorian(jy, 1, 1)
            end_iso = _jmonth_end_iso(jy, 12)
            if end_iso:
                return (f'{gy:04d}-{gm:02d}-{gd:02d}', end_iso + ' 23:59:59')
        except Exception:
            return None
    return None


def _jmonth_end_iso(jy, jm):
    """آخرین روز ماه شمسی → تاریخ ISO (طول ماه دقیق، حتی اسفند کبیسه)"""
    try:
        last = J._j2d(jy, jm + 1, 1) - J._j2d(jy, jm, 1)
        gy, gm, gd = J.to_gregorian(jy, jm, last)
        return f'{gy:04d}-{gm:02d}-{gd:02d}'
    except Exception:
        pass
    # پشتیبان: قاعده عمومی طول ماه‌ها
    day = 31 if jm <= 6 else (30 if jm <= 11 else 29)
    try:
        gy, gm, gd = J.to_gregorian(jy, jm, day)
        return f'{gy:04d}-{gm:02d}-{gd:02d}'
    except Exception:
        return None


def build_group_query(meta, table, sn, group, aggs, where, params, spec, all_cols):
    """کوئری گروه‌بندی/تجمیع"""
    group = [g for g in group if g.get('col') in all_cols][:3]
    agg_cols = []
    for a in aggs:
        col = a.get('col')
        fn = (a.get('fn') or 'count').lower()
        if fn == 'count' and (col in (None, '', '*')):
            agg_cols.append(('COUNT(*)', 'تعداد ردیف', None, 'count'))
            continue
        if col not in all_cols or C.is_sensitive(table, col):
            continue
        fn_map = {'count': 'COUNT', 'sum': 'SUM', 'avg': 'AVG', 'min': 'MIN', 'max': 'MAX'}
        if fn not in fn_map:
            continue
        label = f'{ {"count": "شمارش", "sum": "جمع", "avg": "میانگین", "min": "کمینه", "max": "بیشینه"}[fn] } {C.col_label(table, col)}'
        agg_cols.append((f'{fn_map[fn]}(t{table}."{col}")', label, col, fn))
    if not agg_cols:
        agg_cols.append(('COUNT(*)', 'تعداد', None, 'count'))

    selects, out_cols, post_group = [], [], []
    used_alias = set()
    joins = []
    for gi, g in enumerate(group):
        col, mode = g['col'], g.get('mode') or 'value'
        oc = {'key': col, 'label': C.col_label(table, col), 'kind': 'group'}
        if mode in ('jmonth', 'jyear'):
            fmt = '%Y-%m' if mode == 'jmonth' else '%Y'
            selects.append(f'strftime("{fmt}", t{table}."{col}")')
            oc['label'] += ' (ماه شمسی)' if mode == 'jmonth' else ' (سال شمسی)'
            oc['group_mode'] = mode
        else:
            fkdef = C.FK.get(f'{table}.{col}')
            if fkdef:
                pinfo = meta.get(fkdef['parent'])
                if pinfo:
                    alias = f'g{gi}_{pinfo["sname"]}'
                    if alias not in used_alias:
                        used_alias.add(alias)
                        joins.append(
                            f'LEFT JOIN "{pinfo["sname"]}" AS {alias} ON '
                            f't{table}."{col}" = {alias}."'
                            + ('NID' if fkdef.get('by') == 'nid' else _pk_of(pinfo)) + '"')
                    selects.append(label_expr(fkdef, alias))
                    oc['fk_group'] = col
                else:
                    selects.append(f't{table}."{col}"')
            else:
                selects.append(f't{table}."{col}"')
                oc['dict'] = C.dict_key(table, col) if isinstance(C.dict_key(table, col), (dict, str)) else None
        out_cols.append(oc)
        post_group.append(col)

    selects.extend(expr for expr, _lb, _c, _f in agg_cols)
    for expr, lb, _c, _f in agg_cols:
        out_cols.append({'key': expr, 'label': lb, 'kind': 'agg'})

    gsql = ', '.join(f'{i + 1}' for i in range(len(group)))
    order_sql = ''
    order = spec.get('order') or []
    if order and order[0].get('col'):
        oc = order[0]
        try:
            oi = int(oc['col'])
            direction = 'DESC' if oc.get('dir', 'desc') == 'desc' else 'ASC'
            order_sql = f'ORDER BY {oi} {direction}'
        except (ValueError, TypeError):
            pass
    if not order_sql:
        order_sql = f'ORDER BY {len(group) + 1} DESC'

    limit = min(MAX_EXPORT_ROWS, int(spec.get('limit') or 1000))
    sql = (f'SELECT {", ".join(selects)} FROM "{sn}" AS t{table} {" ".join(joins)} '
           f'WHERE {where} GROUP BY {gsql} {order_sql} LIMIT {limit}')
    return sql, params, out_cols, {'group_cols': [g['col'] for g in group]}, None


# ---------------- اجرا و پس‌پردازش ----------------

def run(conn, meta, dicts, table, spec, translate=True):
    """اجرای گزارش عمومی؛ خروجی استاندارد برای UI و خروجی‌ها"""
    sql, params, out_cols, ginfo, err = build_table_query(meta, table, spec)
    if err:
        return {'error': err}
    t0 = time.time()
    try:
        cur = conn.execute(sql, params or [])
        raw = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        return {'error': f'خطا در اجرای کوئری: {e}', 'sql': sql}
    cols = [c for c in out_cols if not c.get('hidden')]
    rows = []
    for r in raw:
        # حذف ستون‌های خامِ پنهان (FK raw) از نمایش
        vals = []
        ri = 0
        for oc in out_cols:
            v = r[ri] if ri < len(r) else None
            ri += 1
            if oc.get('hidden'):
                continue
            vals.append(transform_value(meta, dicts, table, oc, v, sql_mode=False))
        rows.append(vals)
    # پس‌پردازش گروه‌بندی (ترجمه ماه شمسی)
    if ginfo:
        for gi, gcol in enumerate(ginfo['group_cols']):
            g = (spec.get('group_by') or [{}])[gi] if gi < len(spec.get('group_by') or []) else {}
            if g.get('mode') == 'jmonth':
                for row in rows:
                    mk = J.month_key(row[gi])
                    row[gi] = J.month_label(mk) if mk else ''
            elif g.get('mode') == 'jyear':
                for row in rows:
                    row[gi] = J.fa_num(row[gi])
    return {
        'table': table, 'title': C.table_label(table),
        'columns': [{'key': c['key'], 'label': c['label'], 'kind': c.get('kind')} for c in cols],
        'rows': rows, 'count': len(rows),
        'total_rows': D.table_rows(meta, table),
        'grouped': bool(ginfo),
        'elapsed_ms': int((time.time() - t0) * 1000),
    }


def _pretty(v):
    """نمایش خوانای ستون‌های JSON (مثل EMSType: [\"a\",\"b\"] → a، b)"""
    if isinstance(v, str):
        s = v.strip()
        if s[:1] in ('[', '{') and s[-1:] in (']', '}'):
            try:
                obj = json.loads(s)
                if isinstance(obj, list):
                    return '؛ '.join(str(x) for x in obj) if obj else ''
                if isinstance(obj, dict):
                    return '؛ '.join(f'{k}: {v2}' for k, v2 in obj.items())
            except Exception:
                return v
    return v


def transform_value(meta, dicts, table, oc, v, sql_mode=False):
    """ترجمه یک مقدار برای نمایش"""
    if v is None:
        return ''
    kind = oc.get('kind')
    key = oc.get('key') or ''
    dkey = oc.get('dict')
    if kind == 'date':
        return J.fmt(v)
    if dkey is not None and not oc.get('fk_group'):
        if isinstance(dkey, str) and dkey == 'service':
            return D.service_name(dicts, v, via=oc.get('via'))
        return C.apply_static_dict(dkey, v)
    if kind == 'int':
        try:
            return J.fa_num(f'{int(v):,}')
        except (ValueError, TypeError):
            return str(v)
    if kind == 'decimal':
        try:
            return J.fa_num(f'{float(v):,.1f}')
        except (ValueError, TypeError):
            return str(v)
    return _pretty(str(v))


# ---------------- گزارش‌های آماده ----------------

def run_preset(conn, meta, dicts, preset, params, limit=DEFAULT_DISPLAY_ROWS):
    """اجرای گزارش آماده با پارامترهای فرم فیلتر"""
    where_parts, args = [], []
    for f in preset.get('filters', []):
        key = f['key']
        val = params.get(key)
        if val in (None, '', 'all'):
            continue
        tr = f.get('transform')
        if tr == 'int':
            try:
                val = int(val)
            except (ValueError, TypeError):
                continue
        elif tr == 'jalali_start':
            val = J.jalali_to_iso(val)
            if not val:
                continue
        elif tr == 'jalali_end':
            val = J.jalali_to_iso(val, end_of_day=True)
            if not val:
                continue
        elif tr == 'like':
            val = f'%{val}%'
        elif tr == 'likeboth':
            val = f'%{val}%'
        where_parts.append(f['where'])
        if f.get('multi'):
            args.extend(val if isinstance(val, list) else [val])
        else:
            args.append(val)
    sql = preset['sql'].format(where=(' AND ' + ' AND '.join(where_parts)) if where_parts else '')
    order = preset.get('order', '')
    sql = f'{sql} {order} LIMIT {int(limit)}'
    try:
        raw = conn.execute(sql, args).fetchall()
    except Exception as e:  # noqa: BLE001
        return {'error': f'خطا در اجرای گزارش: {e}', 'sql': sql}
    cols = preset['columns']
    rows = []
    for r in raw:
        row = []
        for ci, c in enumerate(cols):
            v = r[ci] if ci < len(r) else None
            row.append(preset_value(meta, dicts, c, v))
        rows.append(row)
    return {'columns': [{'key': c['key'], 'label': c['label']} for c in cols],
            'rows': rows, 'count': len(rows), 'title': preset['title'],
            'sql': sql, 'args': args}


def preset_value(meta, dicts, c, v):
    if v is None:
        return ''
    typ = c.get('type', 'text')
    if typ == 'date':
        return J.fmt(v, with_time=c.get('time', True))
    if typ == 'jmonth':
        return J.month_label(J.month_key(v)) or ''
    d = c.get('dict')
    if d:
        if d == 'service':
            return D.service_name(dicts, v, via=c.get('via'))
        if d in ('level', 'yn01', 'bit'):
            return C.apply_static_dict(d, v)
        if isinstance(d, dict):
            return C.apply_static_dict(d, v)
    if typ == 'int':
        try:
            return J.fa_num(f'{int(v):,}')
        except (ValueError, TypeError):
            return str(v)
    if typ == 'money':
        try:
            return J.fa_num(f'{int(float(v)):,}')
        except (ValueError, TypeError):
            return str(v)
    if typ == 'decimal':
        try:
            return J.fa_num(f'{float(v):,.1f}')
        except (ValueError, TypeError):
            return str(v)
    return _pretty(str(v))


# مرجع اتصال جاری برای دیکشنری‌های داخل preset_value (ساده و ایمن در این برنامه تک‌کاربره)
_CONN_REF = {'c': None, 'm': None}


def set_conn_ref(conn, meta):
    _CONN_REF['c'] = conn
    _CONN_REF['m'] = meta


# ---------------- خروجی فایل ----------------

def to_csv(columns, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\r\n')
    w.writerow([c['label'] for c in columns])
    for r in rows:
        w.writerow(['' if v is None else str(v) for v in r])
    return '\ufeff' + buf.getvalue()


def to_xlsx(columns, rows, title='گزارش'):
    """خروجی اکسل — ترجیحاً با openpyxl؛ اگر نصب نبود با موتور داخلی (بدون وابستگی)"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        return to_xlsx_basic(columns, rows, title)
    wb = Workbook()
    ws = wb.active
    ws.title = title[:28] or 'گزارش'
    ws.sheet_view.rightToLeft = True
    head_fill = PatternFill('solid', fgColor='E91E63')
    for ci, c in enumerate(columns, 1):
        cell = ws.cell(row=1, column=ci, value=c['label'])
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = head_fill
        cell.alignment = Alignment(horizontal='right')
        ws.column_dimensions[get_column_letter(ci)].width = min(40, max(12, len(c['label']) * 1.6 + 6))
    for ri, row in enumerate(rows, 2):
        for ci, v in enumerate(row, 1):
            cell = ws.cell(row=ri, column=ci, value=v if v != '' else None)
            cell.alignment = Alignment(horizontal='right')
            s = str(v)
            if re.match(r'^\d[\d,]*$', s):
                try:
                    cell.value = int(s.replace(',', ''))
                except ValueError:
                    pass
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------- موتور داخلی XLSX (بدون openpyxl) ----------------

def _xml_escape(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def _sheet_name(title):
    s = re.sub(r'[\[\]\*\?/\\:]', ' ', str(title or 'گزارش')).strip() or 'گزارش'
    return s[:31]


def _col_letter(n):
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


_XLSX_CT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    '</Types>')

_XLSX_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    '</Relationships>')

_XLSX_WB_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>')

_XLSX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Tahoma"/></font>'
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Tahoma"/></font>'
    '</fonts>'
    '<fills count="3">'
    '<fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFE91E63"/><bgColor indexed="64"/></patternFill></fill>'
    '</fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1">'
    '<alignment horizontal="right"/></xf>'
    '</cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    '</styleSheet>')


def to_xlsx_basic(columns, rows, title='گزارش'):
    """ساخت فایل xlsx معتبر فقط با کتابخانه استاندارد (zipfile) — راست‌به‌چپ"""
    name = _sheet_name(title)
    wb = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{_xml_escape(name)}" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>')

    ncols = len(columns)
    nrows = len(rows) + 1
    cols_xml = ''.join(
        f'<col min="{i}" max="{i}" width="{min(45, max(12, len(c["label"]) * 1.6 + 6))}" customWidth="1"/>'
        for i, c in enumerate(columns, 1))

    def cell(ci, v, style=''):
        ref = f'{_col_letter(ci)}{ri}'
        if v is None or v == '':
            return f'<c r="{ref}"{style}/>'
        s = str(v)
        if re.match(r'^\d[\d,]*$', s):
            try:
                return f'<c r="{ref}"{style}><v>{int(s.replace(",", ""))}</v></c>'
            except ValueError:
                pass
        if re.match(r'^-?\d+(\.\d+)?$', s) and len(s) < 16:
            return f'<c r="{ref}"{style}><v>{s}</v></c>'
        return (f'<c r="{ref}"{style} t="inlineStr"><is>'
                f'<t xml:space="preserve">{_xml_escape(s)}</t></is></c>')

    body = ['<row r="1">']
    ri = 1
    for ci, c in enumerate(columns, 1):
        body.append(cell(ci, c['label'], ' s="1"'))
    body.append('</row>')
    for ridx, row in enumerate(rows, 2):
        ri = ridx
        body.append(f'<row r="{ri}">')
        for ci in range(1, min(ncols, len(row)) + 1):
            body.append(cell(ci, row[ci - 1]))
        body.append('</row>')

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{_col_letter(max(1, ncols))}{max(1, nrows)}"/>'
        '<sheetViews><sheetView rightToLeft="1" workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<cols>{cols_xml}</cols>'
        '<sheetData>' + ''.join(body) + '</sheetData>'
        '</worksheet>')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', _XLSX_CT)
        z.writestr('_rels/.rels', _XLSX_RELS)
        z.writestr('xl/workbook.xml', wb)
        z.writestr('xl/_rels/workbook.xml.rels', _XLSX_WB_RELS)
        z.writestr('xl/styles.xml', _XLSX_STYLES)
        z.writestr('xl/worksheets/sheet1.xml', sheet)
    return buf.getvalue()

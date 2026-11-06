# -*- coding: utf-8 -*-
"""سامانه گزارش‌گیری و تحلیل «راه زندگی» — Flask
بر پایه بکاپ MySQL سامانه مراکز خدمات روانشناسی و مشاوره راه زندگی.
"""

import json
import os
import threading
import time
import traceback

from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, url_for)

import bi
import catalog as C
import dbkit as D
import dump_parser
import jalali as J
import presets as P
import repengine as R

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def _basename(p):
    return os.path.basename(str(p))


app.add_template_filter(_basename, 'basename')

_import_lock = threading.Lock()
_import_thread = None
_optimize_thread = None


# ======================================================================
#  ابزارهای مشترک
# ======================================================================

def get_ctx():
    """(conn, meta, dicts) یا (None, None, None)"""
    conn, path = D.connect()
    if conn is None:
        return None, None, None
    meta = D.get_meta(conn)
    dicts = D.dict_services(conn, meta)
    R.set_conn_ref(conn, meta)
    return conn, meta, dicts


def data_ready():
    return D.active_db_path() is not None


def page(template, **kw):
    conn, meta, dicts = get_ctx()
    ready = conn is not None
    kw.setdefault('ready', ready)
    kw.setdefault('db_path', D.active_db_path() or '')
    kw.setdefault('importing', bool(_import_thread and _import_thread.is_alive()))
    if conn:
        try:
            conn.close()
        except Exception:
            pass
    return render_template(template, **kw)


# ======================================================================
#  داشبورد BI
# ======================================================================

@app.route('/')
def dashboard():
    if not data_ready():
        return redirect(url_for('setup'))
    conn, meta, dicts = get_ctx()
    provinces = []
    try:
        provinces = [{'id': k, 'title': v}
                     for k, v in sorted(D.dict_provinces(conn, meta).items(),
                                        key=lambda x: x[1])]
    except Exception:
        pass
    conn.close()
    return page('dashboard.html', provinces=provinces,
                today=J.today_jalali(),
                dashboards=_dashboards_load())


@app.route('/api/bi')
def api_bi():
    if not data_ready():
        return jsonify({'error': 'no-data'}), 503
    conn, meta, dicts = get_ctx()
    try:
        data = bi.build(conn, meta, dicts, {
            'province': request.args.get('province'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        })
        return jsonify(data)
    finally:
        conn.close()


@app.route('/api/bi.csv/<cid>')
def api_bi_csv(cid):
    if not data_ready():
        return Response('no data', 503)
    conn, meta, dicts = get_ctx()
    try:
        csv_text = bi.chart_csv(conn, meta, dicts, cid, {
            'province': request.args.get('province'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        })
    finally:
        conn.close()
    if csv_text is None:
        return Response('not found', 404)
    return Response(csv_text, mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename={cid}.csv'})


# ======================================================================
#  گزارش‌ساز
# ======================================================================

@app.route('/reports')
def reports():
    if not data_ready():
        return redirect(url_for('setup'))
    cats = {}
    for pr in P.PRESETS:
        cats.setdefault(pr['category'], []).append(pr)
    saved = []
    sdir = os.path.join(D.BASE_DIR, 'reports_saved')
    if os.path.isdir(sdir):
        for fn in sorted(os.listdir(sdir)):
            if fn.endswith('.json'):
                try:
                    with open(os.path.join(sdir, fn), encoding='utf-8') as f:
                        spec = json.load(f)
                    saved.append({'name': fn[:-5], 'spec': spec})
                except Exception:
                    pass
    conn, meta, dicts = get_ctx()
    meta_tables = []
    if conn:
        for name, info in meta.items():
            if info['kind'] != 'table':
                continue
            meta_tables.append({'name': name, 'label': C.table_label(name),
                                'rows': info.get('rows') or 0})
        meta_tables.sort(key=lambda t: -t['rows'])
        conn.close()
    saved_specs = {s['name']: s['spec'] for s in saved}
    return page('reports.html', categories=cats, presets=P.PRESETS, saved=saved,
                meta_tables=meta_tables, saved_specs=saved_specs)


@app.route('/api/meta')
def api_meta():
    conn, meta, dicts = get_ctx()
    if conn is None:
        return jsonify({'error': 'no-data'}), 503
    out = []
    for name, info in meta.items():
        if info['kind'] != 'table':
            continue
        cols = []
        for c in info['cols']:
            if C.is_sensitive(name, c):
                continue
            fk = C.FK.get(f'{name}.{c}')
            cols.append({
                'name': c, 'label': C.col_label(name, c),
                'kind': R.col_kind(meta, name, c),
                'fk': bool(fk),
                'dict': (C.dict_key(name, c)
                         if isinstance(C.dict_key(name, c), (dict, str))
                         else ('service' if c == 'ServiceID' and fk else None)),
            })
        out.append({'name': name, 'label': C.table_label(name),
                    'desc': C.table_desc(name), 'rows': info.get('rows') or 0,
                    'cols': cols})
    out.sort(key=lambda t: -t['rows'])
    conn.close()
    return jsonify(out)


@app.route('/api/dicts/<name>')
def api_dicts(name):
    conn, meta, dicts = get_ctx()
    if conn is None:
        return jsonify([])
    out = []
    try:
        if name == 'provinces':
            out = [{'v': k, 't': v} for k, v in
                   sorted(D.dict_provinces(conn, meta).items(), key=lambda x: x[1])]
        elif name == 'cities':
            pid = request.args.get('province')
            if pid:
                try:
                    items = D.dict_cities_by_province(conn, meta).get(int(pid), [])
                except (ValueError, TypeError):
                    items = []
            else:
                items = [{'id': k, 'title': v} for k, v in
                         sorted(D.dict_cities(conn, meta).items(), key=lambda x: x[1])]
            out = [{'v': i['id'], 't': i['title']} for i in items]
        elif name == 'centers':
            out = [{'v': k, 't': v} for k, v in
                   sorted(D.dict_centers(conn, meta).items(), key=lambda x: x[1])]
        elif name == 'services':
            out = [{'v': k, 't': v} for k, v in sorted(dicts.get('by_id', {}).items())]
        elif name == 'services_soha':
            out = [{'v': k, 't': v} for k, v in sorted(dicts.get('by_soha', {}).items())]
    finally:
        conn.close()
    return jsonify(out)


@app.route('/api/report', methods=['POST'])
def api_report():
    conn, meta, dicts = get_ctx()
    if conn is None:
        return jsonify({'error': 'no-data'}), 503
    spec = request.get_json(force=True, silent=True) or {}
    try:
        result = R.run(conn, meta, dicts, spec.get('table'), spec)
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/report/export', methods=['POST'])
def api_report_export():
    conn, meta, dicts = get_ctx()
    if conn is None:
        return Response('no data', 503)
    spec = request.get_json(force=True, silent=True) or {}
    fmt = (spec.get('format') or 'csv').lower()
    spec['limit'] = R.MAX_EXPORT_ROWS
    try:
        result = R.run(conn, meta, dicts, spec.get('table'), spec)
    finally:
        conn.close()
    if result.get('error'):
        return Response(result['error'], 400)
    return _export_response(result['columns'], result['rows'],
                            result.get('title') or 'گزارش', fmt)


def _export_response(columns, rows, title, fmt):
    if fmt == 'xlsx':
        data = R.to_xlsx(columns, rows, title)
        if data:
            return Response(data,
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            headers={'Content-Disposition':
                                     f"attachment; filename=report.xlsx"})
    csv_text = R.to_csv(columns, rows)
    return Response(csv_text, mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             "attachment; filename=report.csv"})


# ---------- گزارش‌های ذخیره‌شده ----------

def _saved_dir():
    d = os.path.join(D.BASE_DIR, 'reports_saved')
    os.makedirs(d, exist_ok=True)
    return d


@app.route('/api/saved', methods=['GET'])
def saved_list():
    out = []
    d = _saved_dir()
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'):
            try:
                with open(os.path.join(d, fn), encoding='utf-8') as f:
                    out.append({'name': fn[:-5], 'spec': json.load(f)})
            except Exception:
                pass
    return jsonify(out)


@app.route('/api/saved', methods=['POST'])
def saved_save():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()[:60]
    spec = data.get('spec') or {}
    if not name or not spec.get('table'):
        return jsonify({'error': 'نام و مشخصات گزارش لازم است'}), 400
    safe = ''.join(ch for ch in name if ch not in '\\/:*?"<>|') or 'report'
    with open(os.path.join(_saved_dir(), safe + '.json'), 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False)
    return jsonify({'ok': True, 'name': safe})


@app.route('/api/saved/<name>', methods=['DELETE'])
def saved_delete(name):
    p = os.path.join(_saved_dir(), os.path.basename(name) + '.json')
    if os.path.isfile(p):
        os.remove(p)
    return jsonify({'ok': True})


# ---------- داشبوردهای شخصی (فیلترهای ذخیره‌شده + نمودارهای سنجاق‌شده) ----------

def _dash_file():
    d = os.path.join(D.BASE_DIR, 'dashboards_saved')
    os.makedirs(d, exist_ok=True)
    return d


def _dashboards_load():
    """فهرست داشبوردها: [{name, filters, pins:[{title, spec}]}]"""
    out = []
    d = _dash_file()
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'):
            try:
                with open(os.path.join(d, fn), encoding='utf-8') as f:
                    item = json.load(f)
                item['name'] = fn[:-5]
                out.append(item)
            except Exception:
                pass
    return out


@app.route('/api/dashboards', methods=['GET'])
def dashboards_list():
    return jsonify(_dashboards_load())


@app.route('/api/dashboards', methods=['POST'])
def dashboards_save():
    data = request.get_json(force=True, silent=True) or {}
    dbs = _dashboards_load()
    # سنجاق کردن نمودار از گزارش‌ساز به داشبورد پیش‌فرض
    if data.get('add_pin'):
        pin = data['add_pin']
        if not isinstance(pin.get('spec'), dict) or not pin['spec'].get('table'):
            return jsonify({'error': 'مشخصات گزارش نامعتبر است'}), 400
        target = dbs[0] if dbs else None
        if target is None:
            target = {'name': 'داشبورد من', 'filters': {}, 'pins': []}
            dbs.append(target)
        target.setdefault('pins', []).append(
            {'title': (pin.get('title') or 'نمودار')[:80], 'spec': pin['spec']})
        _dashboards_write(target)
        return jsonify({'ok': True, 'dashboard': target['name']})
    if isinstance(data.get('remove_pin'), int):
        target = dbs[0] if dbs else None
        if target is None:
            return jsonify({'error': 'داشبوردی وجود ندارد'}), 404
        pins = target.get('pins') or []
        i = data['remove_pin']
        if 0 <= i < len(pins):
            pins.pop(i)
            _dashboards_write(target)
        return jsonify({'ok': True})
    # ذخیره/به‌روزرسانی داشبورد با نام
    name = (data.get('name') or '').strip()[:60]
    if not name:
        return jsonify({'error': 'نام داشبورد لازم است'}), 400
    safe = ''.join(ch for ch in name if ch not in '\\/:*?"<>|') or 'dash'
    item = {'filters': data.get('filters') or {},
            'pins': data.get('pins') or []}
    for db_ in dbs:
        if db_['name'] == safe:
            item['pins'] = db_.get('pins') or item.get('pins') or []
    _dashboards_write(item, safe)
    return jsonify({'ok': True, 'name': safe})


def _dashboards_write(item, name=None):
    d = _dash_file()
    safe = name or ''.join(ch for ch in (item.get('name') or 'داشبورد من')
                           if ch not in '\\/:*?"<>|')
    p = os.path.join(d, os.path.basename(safe) + '.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'filters': item.get('filters') or {},
                   'pins': item.get('pins') or []}, f, ensure_ascii=False)


@app.route('/api/dashboards/<name>', methods=['DELETE'])
def dashboards_delete(name):
    p = os.path.join(_dash_file(), os.path.basename(name) + '.json')
    if os.path.isfile(p):
        os.remove(p)
    return jsonify({'ok': True})


# ---------- گزارش‌های آماده ----------

@app.route('/preset/<key>')
def preset_page(key):
    if not data_ready():
        return redirect(url_for('setup'))
    pr = P.PRESET_BY_KEY.get(key)
    if not pr:
        return page('error.html', message='گزارش پیدا نشد'), 404
    return page('preset.html', preset=pr, key=key, today=J.today_jalali())


@app.route('/api/preset/<key>', methods=['POST'])
def api_preset(key):
    conn, meta, dicts = get_ctx()
    if conn is None:
        return jsonify({'error': 'no-data'}), 503
    pr = P.PRESET_BY_KEY.get(key)
    if not pr:
        conn.close()
        return jsonify({'error': 'گزارش پیدا نشد'}), 404
    params = request.get_json(force=True, silent=True) or {}
    limit = min(R.MAX_EXPORT_ROWS, int(params.pop('limit', 200) or 200))
    try:
        result = _run_preset_full(conn, meta, dicts, pr, params, limit)
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/preset/<key>/export', methods=['POST'])
def api_preset_export(key):
    conn, meta, dicts = get_ctx()
    if conn is None:
        return Response('no data', 503)
    pr = P.PRESET_BY_KEY.get(key)
    if not pr:
        conn.close()
        return Response('not found', 404)
    params = request.get_json(force=True, silent=True) or {}
    fmt = (params.pop('format') or 'csv').lower()
    params.pop('limit', None)
    try:
        result = _run_preset_full(conn, meta, dicts, pr, params, R.MAX_EXPORT_ROWS)
    finally:
        conn.close()
    if result.get('error'):
        return Response(result['error'], 400)
    return _export_response(result['columns'], result['rows'], pr['title'], fmt)


def _run_preset_full(conn, meta, dicts, pr, params, limit):
    """اجرای preset با پشتیبانی فیلترهای ویژه"""
    where_parts, args = [], []
    special = pr.get('special')
    for f in pr.get('filters', []):
        key = f['key']
        val = params.get(key)
        if val in (None, '', 'all'):
            continue
        if special in ('confirm_stage', 'payments_confirm', 'recipient_month') \
                and key in ('stage', 'cstate', 'confirm', 'month'):
            continue  # بعداً جداگانه
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
        elif tr in ('likeboth', 'like'):
            val = f'%{val}%'
        elif tr == 'like2':
            val = [f'%{val}%'] * 2
        elif tr == 'like4':
            val = [f'%{val}%'] * 4
        where_parts.append(f['where'])
        if isinstance(val, list):
            args.extend(val)
        else:
            args.append(val)
    # فیلترهای ویژه
    if special == 'confirm_stage':
        w, a = P.confirm_stage_where(params.get('stage'), params.get('cstate'))
        if w:
            where_parts.append(w)
            if a:
                args.append(a)
    elif special in ('payments_confirm',):
        w = P.all_confirmed_where(params.get('confirm'))
        if w:
            where_parts.append(w)
    elif special == 'recipient_month':
        w = P.all_confirmed_where(params.get('confirm'))
        if w:
            where_parts.append(w)
        mstart = P._jmonth_start(params.get('month'))
        mend = P._jmonth_end(params.get('month'))
        if mstart:
            where_parts.append('AND e.StartDate >= ?')
            args.append(mstart)
        if mend:
            where_parts.append('AND e.StartDate <= ?')
            args.append(mend)
    where_sql = (' ' + ' '.join(where_parts)) if where_parts else ''
    sql = pr['sql'].replace('{where}', where_sql) + ' ' + pr.get('order', '')
    sql += f' LIMIT {int(limit)}'
    t0 = time.time()
    try:
        raw = conn.execute(sql, args).fetchall()
    except Exception as e:  # noqa: BLE001
        return {'error': f'خطا در اجرای گزارش: {e}', 'sql': sql, 'args': args}
    rows = []
    for r in raw:
        row = []
        for ci, c in enumerate(pr['columns']):
            row.append(R.preset_value(meta, dicts, c, r[ci] if ci < len(r) else None))
        rows.append(row)
    return {'columns': pr['columns'], 'rows': rows, 'count': len(rows),
            'title': pr['title'], 'elapsed_ms': int((time.time() - t0) * 1000)}


# ======================================================================
#  مرور داده‌ها
# ======================================================================

@app.route('/tables')
def tables():
    if not data_ready():
        return redirect(url_for('setup'))
    conn, meta, dicts = get_ctx()
    items = []
    for name, info in meta.items():
        if info['kind'] != 'table':
            continue
        items.append({'name': name, 'label': C.table_label(name),
                      'desc': C.table_desc(name), 'rows': info.get('rows') or 0,
                      'cols': len(info['cols'])})
    items.sort(key=lambda t: -t['rows'])
    total = sum(t['rows'] for t in items)
    conn.close()
    return page('tables.html', tables=items, total_rows=total)


@app.route('/table/<name>')
def table_view(name):
    if not data_ready():
        return redirect(url_for('setup'))
    conn, meta, dicts = get_ctx()
    if conn is None or name not in meta:
        conn.close()
        return page('error.html', message=f'جدول «{name}» یافت نشد'), 404
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', '')
    direction = 'desc' if request.args.get('dir', 'asc') == 'desc' else 'asc'
    try:
        page_no = max(1, int(request.args.get('p', 1)))
    except ValueError:
        page_no = 1
    try:
        per_page = int(request.args.get('ps', 50))
    except ValueError:
        per_page = 50
    if per_page not in (25, 50, 100, 200, 500):
        per_page = 50
    info = meta[name]
    # فیلتر ستونی: f_<colname> — پشتیبانی از همه ستون‌ها (تاریخ شمسی هم پشتیبانی می‌شود)
    col_filters, active_filters = [], {}
    for c in info['cols']:
        v = (request.args.get('f_' + c) or '').strip()
        if v:
            col_filters.append({'col': c, 'op': 'contains', 'value': v})
            active_filters[c] = v
    spec = {
        'columns': None,
        'filters': col_filters,
        'search': q,
        'order': ([{'col': sort, 'dir': direction}] if sort else []),
        'limit': per_page,
        'offset': (page_no - 1) * per_page,
    }
    result = R.run(conn, meta, dicts, name, spec)
    # شمارش کل با فیلتر جستجو و فیلتر ستون‌ها
    where_sql, args = R.build_where(meta, name, spec, info['cols'])
    sn = info['sname']
    try:
        total = conn.execute(
            f'SELECT COUNT(*) FROM "{sn}" AS t{name} WHERE {where_sql}', args).fetchone()[0]
    except Exception:
        total = result.get('total_rows') or 0
    pages = max(1, (total + per_page - 1) // per_page)
    if page_no > pages:
        page_no = pages
    fk_cols = {}
    for c in info['cols']:
        f = C.FK.get(f'{name}.{c}')
        if f:
            fk_cols[c] = f
    colmeta = [{'name': c, 'label': C.col_label(name, c),
                'kind': R.col_kind(meta, name, c)} for c in info['cols']]
    conn.close()
    return page('table.html', name=name, label=C.table_label(name),
                desc=C.table_desc(name), result=result, q=q, sort=sort,
                direction=direction, page_no=page_no, pages=pages, total=total,
                fk_cols=fk_cols, dates=C.DATES.get(name, []),
                per_page=per_page, colmeta=colmeta,
                active_filters=active_filters)


def _table_qs(**over):
    """ساخت querystring برای صفحه‌بندی/مرتب‌سازی با حفظ فیلترهای ستونی"""
    from urllib.parse import urlencode
    params = {k: request.args.get(k) for k in request.args if k != 'p'}
    params.update({k: v for k, v in over.items() if v is not None})
    return urlencode({k: v for k, v in params.items() if v})


app.add_template_global(_table_qs, 'table_qs')


@app.route('/table/<name>/export.csv')
@app.route('/table/<name>/export')
def table_export(name):
    if not data_ready():
        return Response('no data', 503)
    conn, meta, dicts = get_ctx()
    if conn is None or name not in meta:
        conn.close()
        return Response('not found', 404)
    info = meta[name]
    col_filters = []
    for c in info['cols']:
        v = (request.args.get('f_' + c) or '').strip()
        if v:
            col_filters.append({'col': c, 'op': 'contains', 'value': v})
    spec = {'columns': None, 'search': request.args.get('q', '').strip(),
            'filters': col_filters,
            'limit': R.MAX_EXPORT_ROWS}
    result = R.run(conn, meta, dicts, name, spec)
    conn.close()
    if result.get('error'):
        return Response(result['error'], 400)
    fmt = 'xlsx' if request.path.endswith('/export') and \
        request.args.get('fmt') != 'csv' else 'csv'
    title = f'{C.table_label(name)} ({name})'
    if fmt == 'xlsx':
        data = R.to_xlsx(result['columns'], result['rows'], title)
        if data:
            return Response(data,
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            headers={'Content-Disposition':
                                     f'attachment; filename={name}.xlsx'})
    csv_text = R.to_csv(result['columns'], result['rows'])
    return Response(csv_text, mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             f'attachment; filename={name}.csv'})


# ======================================================================
#  استعلام مددجو
# ======================================================================

@app.route('/person')
def person():
    if not data_ready():
        return redirect(url_for('setup'))
    nid = (request.args.get('nid') or '').strip()
    if not nid:
        return page('person.html', nid='', data=None)
    conn, meta, dicts = get_ctx()
    try:
        data = _person_data(conn, meta, dicts, nid)
    finally:
        conn.close()
    return page('person.html', nid=nid, data=data)


def _tbl(conn, sql, args=()):
    try:
        return conn.execute(sql, args).fetchall()
    except Exception:
        return []


def _person_data(conn, meta, dicts, nid):
    """پرونده کامل یک کد ملی"""
    nid_clean = nid.strip()
    if not nid_clean.isdigit():
        return {'error': 'کد ملی باید عدد باشد'}
    sn = lambda t: D.sname(meta, t)
    user = None
    for r in _tbl(conn, f'SELECT id, NID, Username, Name, Family, Father, Gender, '
                        f'Birthday, Mobile, Mobile2, Email, ProvinceID, CityID, '
                        f'SignupDate, LastLogin, Blocked, Confirm, EducationID, MarriageID '
                        f'FROM "{sn("Users")}" WHERE NID = ? LIMIT 1', (int(nid_clean),)):
        user = dict(zip(['id', 'nid', 'username', 'name', 'family', 'father', 'gender',
                         'birthday', 'mobile', 'mobile2', 'email', 'province', 'city',
                         'signup', 'lastlogin', 'blocked', 'confirm', 'edu', 'marriage'], r))
        break
    roles = _tbl(conn,
                 f'SELECT ro.Title, ur.Level, ur.StartDate, ur.EndDate, ur.IsSuspended '
                 f'FROM "{sn("UserRoles")}" ur LEFT JOIN "{sn("Roles")}" ro ON ur.RoleID = ro.id '
                 f'WHERE ur.UserID = ?', (user['id'],)) if user else []
    events = _tbl(conn,
                  f'SELECT e.id, e.ServiceID, e.StartDate, e.EndDate, e.EMS, '
                  f'e.CenterID, e.AcceptorID, '
                  f"ac.Name || ' ' || ac.Family, c.CenterTitle, "
                  f"CASE WHEN e.CenterAdminConfirmUserID IS NOT NULL THEN 1 ELSE 0 END + "
                  f"CASE WHEN e.CenterTechConfirmUserID IS NOT NULL THEN 1 ELSE 0 END + "
                  f"CASE WHEN e.OperatorConfirmUserID IS NOT NULL THEN 1 ELSE 0 END + "
                  f"CASE WHEN e.ProvinceSupervisorConfirmUserID IS NOT NULL THEN 1 ELSE 0 END + "
                  f"CASE WHEN e.SupervisorConfirmUserID IS NOT NULL THEN 1 ELSE 0 END "
                  f'FROM "{sn("Events")}" e '
                  f'LEFT JOIN "{sn("Users")}" ac ON e.AcceptorID = ac.id '
                  f'LEFT JOIN "{sn("Centers")}" c ON e.CenterID = c.id '
                  f'WHERE e.NID = ? ORDER BY e.StartDate DESC LIMIT 100', (int(nid_clean),))
    reserves = _tbl(conn,
                    f'SELECT er.id, er.Date, ac.Name || \' \' || ac.Family, er.EventID '
                    f'FROM "{sn("EventReserves")}" er LEFT JOIN "{sn("Users")}" ac ON er.AcceptorID = ac.id '
                    f'WHERE er.UserID = ? ORDER BY er.Date DESC LIMIT 50',
                    (user['id'],)) if user else []
    ems = _tbl(conn,
               f'SELECT ee.id, ee.DateTime, ee.SuicidalRiskLevel, ee.Status, '
               f'ee.HadPaymentAmount, ee.HadPaymentStatus '
               f'FROM "{sn("EventsEms")}" ee LEFT JOIN "{sn("Events")}" e ON ee.EventID = e.id '
               f'WHERE e.NID = ? ORDER BY ee.DateTime DESC LIMIT 30', (int(nid_clean),))
    referrs = _tbl(conn,
                   f'SELECT r.id, r.RefID, r.ServiceID, r.Status, r.Type, r.CreationDate '
                   f'FROM "{sn("Referrs")}" r LEFT JOIN "{sn("Users")}" u ON r.UserID = u.id '
                   f'WHERE u.NID = ? ORDER BY r.CreationDate DESC LIMIT 30', (int(nid_clean),))
    sms = _tbl(conn,
               f'SELECT s.id, s.Number, s.Message, s.Status, s.CreateTime '
               f'FROM "{sn("SMS")}" s LEFT JOIN "{sn("Users")}" u ON s.SmsReceiver = u.id '
               f'WHERE u.NID = ? ORDER BY s.CreateTime DESC LIMIT 30', (int(nid_clean),))
    taxes = _tbl(conn,
                 f'SELECT t.Year, t.Month, t.TaxAmount, t.TotalPayment, t.ExemptionMonths '
                 f'FROM "{sn("ConsultantTax")}" t WHERE t.NID = ? '
                 f'ORDER BY t.Year DESC, t.Month DESC LIMIT 24', (int(nid_clean),))
    career = _tbl(conn,
                  f'SELECT cc.id, cc.ApplicationDate, cc.TargetGroup, cc.Status, cc.Office '
                  f'FROM "{sn("CareerCounseling")}" cc WHERE cc.ApplicantNID = ? '
                  f'ORDER BY cc.ApplicationDate DESC LIMIT 20', (int(nid_clean),))

    prov = D.dict_provinces(conn, meta)
    mar = D.dict_simple(conn, meta, 'Marriage')
    edu = D.dict_simple(conn, meta, 'Education')
    by_id = dicts.get('by_id', {})
    centers = D.dict_centers(conn, meta)

    def jn(v, with_time=True):
        return J.fmt(v, with_time=with_time) if v else '—'

    def svc(v):
        try:
            return by_id.get(int(v), f'خدمت {v}')
        except (TypeError, ValueError):
            return f'خدمت {v}'

    def ctr(v):
        try:
            return centers.get(int(v), '—')
        except (TypeError, ValueError):
            return '—'

    out = {
        'user': None if not user else {
            **{k: user[k] for k in ('id', 'nid', 'username', 'name', 'family', 'father',
                                    'mobile', 'mobile2', 'email')},
            'gender': C.apply_static_dict({'male': 'مرد', 'female': 'زن'}, user['gender']),
            'birthday': jn(user['birthday'], False),
            'province': prov.get(user['province'], '—'),
            'marriage': mar.get(user['marriage'], '—') if user['marriage'] else '—',
            'edu': edu.get(user['edu'], '—') if user['edu'] else '—',
            'signup': jn(user['signup']), 'lastlogin': jn(user['lastlogin']),
            'blocked': C.apply_static_dict('yn01', user['blocked']),
            'confirm': C.apply_static_dict('yn01', user['confirm']),
        },
        'roles': [{'title': r[0], 'level': C.apply_static_dict('level', r[1]),
                   'start': jn(r[2], False), 'end': jn(r[3], False),
                   'suspended': C.apply_static_dict('yn01', r[4])} for r in roles],
        'events': [{'id': r[0], 'service': svc(r[1]), 'start': jn(r[2]), 'end': jn(r[3]),
                    'ems': C.apply_static_dict('bit', r[4]), 'center': ctr(r[5]),
                    'adviser': r[7] or '—', 'confirms': J.fa_num(r[9] or 0)}
                   for r in events],
        'reserves': [{'id': r[0], 'date': jn(r[1]), 'adviser': r[2] or '—', 'event': r[3]}
                     for r in reserves],
        'ems': [{'id': r[0], 'date': jn(r[1]),
                 'risk': C.apply_static_dict(
                     {'low': 'کم', 'medium': 'متوسط', 'high': 'بالا', 'norisk': 'بدون خطر'}, r[2]),
                 'status': C.apply_static_dict(
                     {'Pending': 'در انتظار بررسی', 'inProgress': 'در حال بررسی',
                      'Done': 'تایید شده', 'Reject': 'رد شده'}, r[3]),
                 'amount': J.fa_num(f'{(r[4] or 0):,}') if r[4] else '—',
                 'pay': r[5] or '—'} for r in ems],
        'referrs': [{'id': r[0], 'refid': r[1], 'service': svc(r[2]),
                     'status': C.apply_static_dict(
                         {'Pending': 'در انتظار', 'inProgress': 'در جریان', 'Done': 'انجام شده'}, r[3]),
                     'type': C.apply_static_dict({'soha': 'سها', 'inPerson': 'حضوری'}, r[4]),
                     'date': jn(r[5])} for r in referrs],
        'sms': [{'id': r[0], 'number': r[1], 'message': (r[2] or '')[:120],
                 'status': C.apply_static_dict(
                     {'Pending': 'در صف', 'Failed': 'ناموفق', 'Success': 'موفق'}, r[3]),
                 'date': jn(r[4])} for r in sms],
        'taxes': [{'year': J.fa_num(r[0]), 'month': J.fa_num(r[1]),
                   'tax': J.fa_num(f'{(r[2] or 0):,}'), 'total': J.fa_num(f'{(r[3] or 0):,}'),
                   'exempt': J.fa_num(r[4] or 0)} for r in taxes],
        'career': [{'id': r[0], 'date': jn(r[1], False), 'target': r[2] or '—',
                    'status': r[3] or '—', 'office': r[4] or '—'} for r in career],
        'error': None,
    }
    if user is None:
        out['error'] = 'کاربری با این کد ملی یافت نشد (بر اساس جلسات/ارجاع‌ها جستجو شود)'
        # حتی بدون پروفایل، جلسات با NID ممکن است باشد
        if not events and not referrs:
            return out
    return out


# ======================================================================
#  راه‌اندازی / ایمپورت / بهینه‌سازی
# ======================================================================

@app.route('/setup')
def setup():
    sources = D.discover_sources()
    current = D.active_db_path()
    cfg = D.load_config()
    return page('setup.html', sources=sources, current=current, cfg=cfg,
                status=_read_status())


def _read_status():
    try:
        with open(D.STATUS_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'state': 'idle'}


@app.route('/api/status')
def api_status():
    st = _read_status()
    st['importing'] = bool(_import_thread and _import_thread.is_alive())
    st['optimizing'] = bool(_optimize_thread and _optimize_thread.is_alive())
    st['active_db'] = D.active_db_path()
    if not (st.get('importing') or st.get('optimizing')):
        if st.get('state') in ('importing', 'optimizing'):
            st['state'] = 'done' if st.get('state') == 'importing' else st.get('state')
    return jsonify(st)


@app.route('/api/use_db', methods=['POST'])
def api_use_db():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get('path') or ''
    if not os.path.isfile(path):
        return jsonify({'error': 'فایل پیدا نشد'}), 400
    D.save_config({'db_path': path, 'source': 'existing'})
    D.clear_dict_cache()
    bi._cache.clear()
    return jsonify({'ok': True})


@app.route('/api/import_sql', methods=['POST'])
def api_import_sql():
    global _import_thread
    data = request.get_json(force=True, silent=True) or {}
    path = data.get('path') or ''
    if not os.path.isfile(path):
        return jsonify({'error': 'فایل بکاپ پیدا نشد'}), 400
    with _import_lock:
        if _import_thread and _import_thread.is_alive():
            return jsonify({'error': 'استخراج دیگری در جریان است'}), 409
        os.makedirs(os.path.dirname(D.OWN_DB), exist_ok=True)
        imp = dump_parser.Importer(path, D.OWN_DB, D.STATUS_PATH)

        def worker():
            imp.run()
            if imp.status.get('state') == 'done':
                D.save_config({'db_path': D.OWN_DB, 'source': 'imported'})
                D.clear_dict_cache()
                bi._cache.clear()
        _import_thread = threading.Thread(target=worker, daemon=True,
                                          name='import-sql')
        _import_thread.start()
    return jsonify({'ok': True})


@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    """ساخت ایندکس‌ها برای سرعت گزارش‌ها — روی دیتابیس فعال"""
    global _optimize_thread
    path = D.active_db_path()
    if not path:
        return jsonify({'error': 'منبع داده‌ای تنظیم نشده'}), 400
    if _optimize_thread and _optimize_thread.is_alive():
        return jsonify({'error': 'بهینه‌سازی در جریان است'}), 409

    idx = [
        ('ix_events_nid', 'Events', 'NID'),
        ('ix_events_user', 'Events', 'UserID'),
        ('ix_events_acceptor', 'Events', 'AcceptorID'),
        ('ix_events_center', 'Events', 'CenterID'),
        ('ix_events_service', 'Events', 'ServiceID'),
        ('ix_events_start', 'Events', 'StartDate'),
        ('ix_events_refid', 'Events', 'RefID'),
        ('ix_gevents_start', 'GroupEvents', 'StartDate'),
        ('ix_gevents_group', 'GroupEvents', 'GroupID'),
        ('ix_reserves_user', 'EventReserves', 'UserID'),
        ('ix_reserves_date', 'EventReserves', 'Date'),
        ('ix_users_nid', 'Users', 'NID'),
        ('ix_users_signup', 'Users', 'SignupDate'),
        ('ix_referrs_user', 'Referrs', 'UserID'),
        ('ix_referrs_date', 'Referrs', 'CreationDate'),
        ('ix_rr_user', 'ReferrsRequest', 'UserID'),
        ('ix_ems_event', 'EventsEms', 'EventID'),
        ('ix_ems_date', 'EventsEms', 'DateTime'),
        ('ix_log_uid', 'Log', 'uid'),
        ('ix_log_ts', 'Log', 'Timestamp'),
        ('ix_sms_time', 'SMS', 'CreateTime'),
        ('ix_gemm_gevent', 'GroupEventMember', 'GroupEventID'),
        ('ix_gm_group', 'GroupMembers', 'GroupID'),
    ]

    def worker():
        st = {'state': 'optimizing', 'phase': 'ساخت ایندکس‌ها…', 'percent': 0,
              'error': None, 'done': 0, 'total': len(idx)}
        _save_status(st)
        try:
            conn = sqlite3_connect_rw(path)
            conn.execute('PRAGMA journal_mode=WAL')
            for i, (iname, tbl, col) in enumerate(idx):
                try:
                    sn = _resolve_sname(conn, tbl)
                    if sn:
                        conn.execute(f'CREATE INDEX IF NOT EXISTS "{iname}" '
                                     f'ON "{sn}" ("{col}")')
                except Exception:
                    pass
                st['done'] = i + 1
                st['percent'] = int((i + 1) * 100 / len(idx))
                _save_status(st, force=True)
            conn.commit()
            conn.close()
            st.update(state='done', phase='ایندکس‌ها ساخته شد', percent=100)
        except Exception as e:  # noqa: BLE001
            st['state'] = 'error'
            st['error'] = str(e)[:300]
        _save_status(st, force=True)

    _optimize_thread = threading.Thread(target=worker, daemon=True, name='optimize')
    _optimize_thread.start()
    return jsonify({'ok': True})


def sqlite3_connect_rw(path):
    import sqlite3
    return sqlite3.connect(path, timeout=60)


def _resolve_sname(conn, logical):
    try:
        row = conn.execute('SELECT sname FROM _meta WHERE name = ?', (logical,)).fetchone()
        if row:
            return row[0]
    except Exception:
        pass
    return logical


def _save_status(st, force=False):
    try:
        os.makedirs(os.path.dirname(D.STATUS_PATH), exist_ok=True)
        tmp = D.STATUS_PATH + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False)
        try:
            os.replace(tmp, D.STATUS_PATH)
        except OSError:
            with open(D.STATUS_PATH, 'w', encoding='utf-8') as f:
                json.dump(st, f, ensure_ascii=False)
    except Exception:
        pass


@app.route('/api/remove_source', methods=['POST'])
def api_remove_source():
    D.save_config({})
    return jsonify({'ok': True})


@app.errorhandler(404)
def not_found(e):
    return page('error.html', message='صفحه پیدا نشد'), 404


@app.errorhandler(500)
def server_error(e):
    if app.debug:
        raise e
    return page('error.html', message='خطای داخلی سرور'), 500


if __name__ == '__main__':
    os.makedirs(os.path.join(D.BASE_DIR, 'data'), exist_ok=True)
    print('=' * 60)
    print('  سامانه گزارش‌گیری راه زندگی — آدرس: http://127.0.0.1:5000')
    print('=' * 60)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

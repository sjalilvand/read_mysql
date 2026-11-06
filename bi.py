# -*- coding: utf-8 -*-
"""داشبورد مدیریتی BI — کوئری‌های آماری با کش زمانی.

همه آمارها از همان دیتابیس استخراج‌شده بکاپ ساخته می‌شوند؛ فیلترهای
استان و بازه تاریخ (شمسی) روی بخش اصلی اعمال می‌شود.
"""

import time

import jalali as J

_cache = {}
TTL = 300  # ثانیه

PALETTE = ['#e91e63', '#2563eb', '#16a34a', '#d97706', '#7c3aed', '#0891b2',
           '#dc2626', '#4d7c0f', '#be185d', '#475569', '#b45309', '#0f766e']


def _num(v, nd=1):
    """تبدیل امن به عدد برای قالب‌بندی (مقادیر ممکن است TEXT باشند)"""
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _q(conn, sql, args=()):
    try:
        return conn.execute(sql, args).fetchall()
    except Exception:
        return []


def _scalar(conn, sql, args=()):
    rows = _q(conn, sql, args)
    if not rows or rows[0][0] is None:
        return 0
    return rows[0][0]


def _donut(rows, cid, title, top=8, dict_fn=None):
    rows = [r for r in rows if r[0] not in (None, '')]
    agg = {}
    for k, v in rows:
        key = dict_fn(k) if dict_fn else str(k)
        agg[key] = agg.get(key, 0) + int(v or 0)
    items = sorted(agg.items(), key=lambda x: -x[1])
    head = items[:top]
    rest = sum(v for _k, v in items[top:])
    labels = [k for k, _v in head]
    values = [v for _k, v in head]
    if rest:
        labels.append('سایر')
        values.append(rest)
    if not values:
        return None
    return {'kind': 'donut', 'id': cid, 'title': title,
            'labels': labels, 'values': values, 'total': sum(values)}


def _bars(rows, cid, title, top=12, dict_fn=None, value_label='تعداد'):
    rows = [r for r in rows if r[0] not in (None, '')]
    agg = {}
    for k, v in rows:
        key = dict_fn(k) if dict_fn else str(k)
        agg[key] = agg.get(key, 0) + int(v or 0)
    items = sorted(agg.items(), key=lambda x: -x[1])[:top]
    if not items:
        return None
    return {'kind': 'bars', 'id': cid, 'title': title, 'value_label': value_label,
            'labels': [k for k, _v in items], 'values': [v for _k, v in items]}


def _line(months, series, cid, title):
    if not months:
        return None
    labels = [J.month_label(m) for m in months]
    return {'kind': 'line', 'id': cid, 'title': title, 'labels': labels,
            'series': series}


def _monthly(conn, sql, args, cid, title, colors=None):
    """خروجی گروه‌بندی ماهانه (strftime %Y-%m) → نمودار خطی با برچسب شمسی"""
    rows = _q(conn, sql, args)
    if not rows:
        return None
    per, months = {}, {}
    for r in rows:
        mk = J.month_key(r[0])
        if not mk:
            continue
        if mk not in months:
            months[mk] = len(months)
        for i in range(1, len(r)):
            per.setdefault(i, {})[mk] = per.get(i, {}).get(mk, 0) + int(r[i] or 0)
    mkeys = sorted(months)
    series = []
    for i in range(1, len(rows[0])):
        name = {1: 'کل', 2: 'انجام‌شده', 3: 'ناتمام'}.get(i, f'سری {i}')
        series.append({'name': name, 'values': [per.get(i, {}).get(mk, 0) for mk in mkeys],
                       'color': (colors or PALETTE)[(i - 1) % len(PALETTE)]})
    return _line(mkeys, series, cid, title)


def build(conn, meta, dicts, params=None):
    """ساخت کامل داده داشبورد"""
    params = params or {}
    province = None
    try:
        province = int(params.get('province')) if params.get('province') else None
    except (TypeError, ValueError):
        province = None
    dfrom = J.jalali_to_iso(params.get('date_from') or '')
    dto = J.jalali_to_iso(params.get('date_to') or '', end_of_day=True)

    ck = (province, dfrom, dto)
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]

    ev_args, ev_where = [], []
    if province:
        ev_where.append('e.CenterID IN (SELECT id FROM Centers WHERE ProvinceID = ?)')
        ev_args.append(province)
    if dfrom:
        ev_where.append('e.StartDate >= ?')
        ev_args.append(dfrom)
    if dto:
        ev_where.append('e.StartDate <= ?')
        ev_args.append(dto)
    W = (' AND ' + ' AND '.join(ev_where)) if ev_where else ''
    A = list(ev_args)

    kpis = []

    def kpi(label, value, sub=None, icon='', tone=''):
        kpis.append({'label': label, 'value': J.fa_num(f'{int(value or 0):,}'),
                     'sub': sub, 'icon': icon, 'tone': tone})

    kpi('کل جلسات مشاوره', _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE 1=1{W}', A),
        'همه جلسات ثبت‌شده', '🗓️', 'p')
    kpi('انجام‌شده', _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE e.EndDate IS NOT NULL{W}', A),
        'جلسات پایان‌یافته', '✅', 'g')
    kpi('ناتمام', _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE e.EndDate IS NULL{W}', A),
        'در جریان یا ردشده', '⏳', 'o')
    kpi('موارد حاد', _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE e.EMS = 1{W}', A),
        'کیس‌های حاد (آسیب به خود)', '🚨', 'r')
    kpi('مراجعان یکتا', _scalar(conn, f'SELECT COUNT(DISTINCT e.NID) FROM Events e WHERE 1=1{W}', A),
        'کدهای ملی متمایز', '🧑', 'b')
    kpi('مشاوران فعال', _scalar(conn, f'SELECT COUNT(DISTINCT e.AcceptorID) FROM Events e WHERE e.AcceptorID > 0{W}', A),
        'مشاوران دارای جلسه', '🧑‍⚕️', 'b')
    kpi('جمع حق‌الزحمه مشاوران (ریال)',
        _scalar(conn, f'SELECT SUM(e.AcceptorFee) FROM Events e WHERE 1=1{W}', A),
        'بر اساس مبلغ ثبت‌شده جلسات', '💰', 'g')
    kpi('رزروهای ثبت‌شده', _scalar(conn, 'SELECT COUNT(*) FROM EventReserves'), None, '📌', 'p')

    charts = []

    # ۱) روند ماهانه جلسات
    c = _monthly(conn,
                 f"SELECT e.StartDate, COUNT(*), "
                 f"SUM(CASE WHEN e.EndDate IS NOT NULL THEN 1 ELSE 0 END) "
                 f"FROM Events e WHERE e.StartDate IS NOT NULL{W} GROUP BY strftime('%Y-%m', e.StartDate) "
                 f"ORDER BY 1", A, 'ev_trend', 'روند ماهانه جلسات مشاوره')
    if c:
        charts.append(c)

    # ۲) نوع خدمت
    rows = _q(conn, f'SELECT e.ServiceID, COUNT(*) FROM Events e WHERE 1=1{W} '
                    'GROUP BY e.ServiceID', A)
    by_id = dicts.get('by_id', {})
    c = _donut(rows, 'ev_service', 'جلسات به تفکیک نوع خدمت',
               dict_fn=lambda k: by_id.get(k if isinstance(k, int) else int(k) if str(k).isdigit() else -1, f'خدمت {k}'))
    if c:
        charts.append(c)

    # ۳) استان‌ها
    rows = _q(conn, f'SELECT c.ProvinceTitle, COUNT(*) FROM Events e '
                    'LEFT JOIN Centers c ON e.CenterID = c.id WHERE 1=1' + W +
                    ' GROUP BY c.ProvinceTitle', A)
    c = _bars(rows, 'ev_province', 'جلسات به تفکیک استان', top=31, value_label='جلسات')
    if c:
        charts.append(c)

    # ۴) مراکز پرتقاضا
    rows = _q(conn, f'SELECT c.CenterTitle, COUNT(*) FROM Events e '
                    'LEFT JOIN Centers c ON e.CenterID = c.id WHERE 1=1' + W +
                    ' GROUP BY c.CenterTitle', A)
    c = _bars(rows, 'ev_center', 'پرتقاضاترین مراکز', top=12, value_label='جلسات')
    if c:
        charts.append(c)

    # ۵) وضعیت تایید ۵ مرحله‌ای
    stages = [('CenterAdminConfirmUserID', 'مدیر مرکز'),
              ('CenterTechConfirmUserID', 'مسئول فنی'),
              ('OperatorConfirmUserID', 'نظارت حرفه‌ای'),
              ('ProvinceSupervisorConfirmUserID', 'ناظر استان'),
              ('SupervisorConfirmUserID', 'ناظر کشور')]
    ok_vals, pend_vals = [], []
    for col, name in stages:
        ok = _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE e.{col} IS NOT NULL' + W, A)
        tot = _scalar(conn, f'SELECT COUNT(*) FROM Events e WHERE 1=1' + W, A)
        ok_vals.append(ok)
        pend_vals.append(max(0, tot - ok))
    if any(v for v in ok_vals) or any(v for v in pend_vals):
        charts.append({'kind': 'bars2', 'id': 'ev_confirm',
                       'title': 'وضعیت تایید ۵ مرحله‌ای جلسات',
                       'labels': [n for _c, n in stages],
                       'values': ok_vals, 'values2': pend_vals,
                       'label_ok': 'تاییدشده', 'label_wait': 'در انتظار',
                       'value_label': 'جلسات'})

    # ۶) جنسیت مراجعان
    rows = _q(conn, f'SELECT u.Gender, COUNT(*) FROM Events e '
                    'LEFT JOIN Users u ON e.UserID = u.id WHERE 1=1' + W +
                    ' GROUP BY u.Gender', A)
    c = _donut(rows, 'ev_gender', 'مراجعان به تفکیک جنسیت',
               dict_fn=lambda k: {'male': 'مرد', 'female': 'زن'}.get(str(k), 'نامشخص'))
    if c:
        charts.append(c)

    # ۷) وضعیت تاهل مراجعان
    rows = _q(conn, f'SELECT u.MarriageID, COUNT(*) FROM Events e '
                    'LEFT JOIN Users u ON e.UserID = u.id WHERE 1=1' + W +
                    ' GROUP BY u.MarriageID', A)
    mar = {}
    try:
        mar = dict(conn.execute('SELECT id, Name FROM Marriage').fetchall())
    except Exception:
        pass
    c = _donut(rows, 'ev_marriage', 'مراجعان به تفکیک وضعیت تاهل',
               dict_fn=lambda k: mar.get(k if isinstance(k, int) else int(k) if str(k).isdigit() else -1, 'نامشخص'))
    if c:
        charts.append(c)

    # ۸) تحصیلات مراجعان
    rows = _q(conn, f'SELECT u.EducationID, COUNT(*) FROM Events e '
                    'LEFT JOIN Users u ON e.UserID = u.id WHERE 1=1' + W +
                    ' GROUP BY u.EducationID', A)
    edu = {}
    try:
        edu = dict(conn.execute('SELECT id, Name FROM Education').fetchall())
    except Exception:
        pass
    c = _donut(rows, 'ev_edu', 'مراجعان به تفکیک تحصیلات',
               dict_fn=lambda k: edu.get(k if isinstance(k, int) else int(k) if str(k).isdigit() else -1, 'نامشخص'))
    if c:
        charts.append(c)

    # ۹) مشاوران پرکار
    rows = _q(conn, f'SELECT a.Name || \' \' || a.Family, COUNT(*) FROM Events e '
                    'LEFT JOIN Users a ON e.AcceptorID = a.id '
                    "WHERE e.AcceptorID > 0" + W + ' GROUP BY a.id', A)
    c = _bars(rows, 'ev_advisers', 'مشاوران پرکار', top=12, value_label='جلسات')
    if c:
        charts.append(c)

    # ۱۰) موارد حاد — شدت خطر و وضعیت
    ew_args, ew = [], []
    if province:
        ew.append('e.CenterID IN (SELECT id FROM Centers WHERE ProvinceID = ?)')
        ew_args.append(province)
    if dfrom:
        ew.append('ee.DateTime >= ?')
        ew_args.append(dfrom)
    if dto:
        ew.append('ee.DateTime <= ?')
        ew_args.append(dto)
    WE = (' AND ' + ' AND '.join(ew)) if ew else ''
    AE = list(ew_args)
    rows = _q(conn, 'SELECT ee.SuicidalRiskLevel, COUNT(*) FROM EventsEms ee '
                    'LEFT JOIN Events e ON ee.EventID = e.id WHERE 1=1' + WE +
                    ' GROUP BY ee.SuicidalRiskLevel', AE)
    c = _donut(rows, 'ems_risk', 'موارد حاد به تفکیک شدت خطر',
               dict_fn=lambda k: {'low': 'کم', 'medium': 'متوسط', 'high': 'بالا',
                                  'norisk': 'بدون خطر'}.get(str(k), 'نامشخص'))
    if c:
        charts.append(c)
    rows = _q(conn, 'SELECT ee.Status, COUNT(*) FROM EventsEms ee '
                    'LEFT JOIN Events e ON ee.EventID = e.id WHERE 1=1' + WE +
                    ' GROUP BY ee.Status', AE)
    c = _donut(rows, 'ems_status', 'موارد حاد به تفکیک وضعیت بررسی',
               dict_fn=lambda k: {'Pending': 'در انتظار بررسی', 'inProgress': 'در حال بررسی',
                                  'Done': 'تایید شده', 'Reject': 'رد شده'}.get(str(k), 'نامشخص'))
    if c:
        charts.append(c)

    # ۱۱) رشد ثبت‌نام کاربران
    c = _monthly(conn, "SELECT u.SignupDate, COUNT(*) FROM Users u "
                       "WHERE u.SignupDate IS NOT NULL GROUP BY strftime('%Y-%m', u.SignupDate) "
                       "ORDER BY 1", [], 'users_trend', 'رشد ثبت‌نام کاربران')
    if c:
        charts.append(c)

    # ۱۲) ارجاعات سها به تفکیک وضعیت
    rows = _q(conn, 'SELECT r.Status, COUNT(*) FROM Referrs r WHERE 1=1 '
                    + (' AND r.ProvinceID = ?' if province else '') +
                    ' GROUP BY r.Status',
               [province] if province else [])
    c = _donut(rows, 'ref_status', 'ارجاع‌های سها به تفکیک وضعیت',
               dict_fn=lambda k: {'Pending': 'در انتظار', 'inProgress': 'در جریان',
                                  'Done': 'انجام شده'}.get(str(k), 'نامشخص'))
    if c:
        charts.append(c)

    # ۱۳) پیامک‌ها
    rows = _q(conn, 'SELECT s.Status, COUNT(*) FROM SMS s GROUP BY s.Status')
    c = _donut(rows, 'sms_status', 'پیامک‌ها به تفکیک وضعیت',
               dict_fn=lambda k: {'Pending': 'در صف', 'Failed': 'ناموفق',
                                  'Success': 'موفق'}.get(str(k), 'نامشخص'))
    if c:
        charts.append(c)

    # ۱۴) جلسات گروهی ماهانه
    c = _monthly(conn, "SELECT ge.StartDate, COUNT(*) FROM GroupEvents ge "
                       "WHERE ge.StartDate IS NOT NULL GROUP BY strftime('%Y-%m', ge.StartDate) "
                       "ORDER BY 1", [], 'group_trend', 'روند ماهانه جلسات گروهی')
    if c:
        charts.append(c)

    # ۱۵) جدول سهمیه‌ها
    budget_rows = _q(conn,
                     'SELECT Title, Type, Amount, Used, Reserved, Remained, '
                     "ROUND(CASE WHEN Amount > 0 THEN Used * 100.0 / Amount ELSE 0 END, 1), "
                     'StartDate, EndDate FROM Budget ORDER BY Id')
    budget = {
        'kind': 'table', 'id': 'budgets', 'title': 'سهمیه‌های خدمات (بودجه)',
        'headers': ['عنوان', 'نوع', 'سقف', 'استفاده‌شده', 'رزرو', 'مانده', 'درصد مصرف', 'شروع', 'پایان'],
        'rows': [[r[0],
                  {'Main': 'خدمات فردی', 'Group': 'خدمات گروهی', 'Job': 'مشاوره شغلی'}.get(r[1], r[1] or '—'),
                  J.fa_num(f'{_num(r[2]):,.1f}'), J.fa_num(f'{_num(r[3]):,.1f}'),
                  J.fa_num(f'{_num(r[4]):,.1f}'), J.fa_num(f'{_num(r[5]):,.1f}'),
                  J.fa_num(f'{_num(r[6]):,.1f}') + '٪',
                  J.fmt(r[7], with_time=False), J.fmt(r[8], with_time=False)]
                 for r in budget_rows],
    }

    result = {
        'generated': J.fmt(time.strftime('%Y-%m-%d %H:%M:%S')),
        'filters': {'province': province, 'date_from': params.get('date_from') or '',
                    'date_to': params.get('date_to') or ''},
        'kpis': kpis, 'charts': charts, 'budget_table': budget,
    }
    _add_insights(result, params)
    _cache[ck] = (time.time(), result)
    if len(_cache) > 20:
        _cache.pop(next(iter(_cache)))
    return result


def _fa_pct(x):
    return J.fa_num(f'{x:,.1f}') + '٪'


def _add_insights(data, params):
    """تفسیر خودکار هر نمودار — تحلیل توصیفی کوتاه فارسی زیر هر نمودار"""
    for ch in data.get('charts', []):
        try:
            ins = None
            if ch['kind'] in ('donut', 'bars') and ch.get('values'):
                vals = ch['values']
                labels = ch['labels']
                total = sum(vals) or 1
                top_i = max(range(len(vals)), key=lambda i: vals[i])
                share = vals[top_i] * 100.0 / total
                top_txt = f'بیشترین سهم با «{labels[top_i]}» و {_fa_pct(share)} از کل است'
                if len(vals) > 1 and vals[top_i] > 0:
                    second = sorted(range(len(vals)), key=lambda i: -vals[i])[1]
                    ratio = vals[top_i] / vals[second] if vals[second] else 0
                    if ratio >= 2:
                        top_txt += f' (حدود {J.fa_num(round(ratio * 10) / 10)} برابر مورد بعدی)'
                ins = top_txt + '.'
            elif ch['kind'] in ('bars2',) and ch.get('series'):
                s0 = ch['series'][0]
                vals, labels = s0['values'], ch.get('labels') or []
                if vals:
                    total = sum(vals) or 1
                    top_i = max(range(len(vals)), key=lambda i: vals[i])
                    ins = (f'بیشترین مقدار «{s0["name"]}» در «{labels[top_i] if top_i < len(labels) else "—"}» '
                           f'با {_fa_pct(vals[top_i] * 100.0 / total)} از جمع است.')
            elif ch['kind'] == 'line' and ch.get('series'):
                s0 = ch['series'][0]
                vals = [v for v in s0['values']]
                labels = ch.get('labels') or []
                if len(vals) >= 2:
                    first, last = vals[0], vals[-1]
                    peak_i = max(range(len(vals)), key=lambda i: vals[i])
                    trend = 'صعودی' if last > first else ('نزولی' if last < first else 'ثابت')
                    chg = f'{(last - first) * 100.0 / first:,.0f}' if first else '—'
                    ins = (f'روند {trend} — از {J.fa_num(first)} به {J.fa_num(last)}'
                           + (f' ({J.fa_num(chg)}٪ تغییر)' if chg != '—' else '')
                           + f'؛ اوج در «{labels[peak_i] if peak_i < len(labels) else "—"}»'
                             f' با {J.fa_num(vals[peak_i])}.')
                    if s0.get('name') == 'کل' and len(ch['series']) > 1:
                        s1 = ch['series'][1]['values']
                        denom = sum(vals) or 1
                        rate = sum(s1) * 100.0 / denom
                        ins += f' نرخ انجام کل: {_fa_pct(rate)}.'
            if params.get('date_from') or params.get('date_to'):
                ins = (ins + ' ') if ins else ''
                ins += '(در بازه فیلتر انتخابی)'
            if ins:
                ch['insight'] = ins
        except Exception:
            continue


def chart_csv(conn, meta, dicts, cid, params=None):
    """خروجی CSV یک نمودار برای دانلود"""
    data = build(conn, meta, dicts, params)
    import io
    import csv as _csv
    for ch in data.get('charts', []):
        if ch.get('id') == cid:
            buf = io.StringIO()
            w = _csv.writer(buf, lineterminator='\r\n')
            if ch['kind'] in ('donut', 'bars', 'bars2'):
                w.writerow(['عنوان', 'تعداد'])
                for i, lb in enumerate(ch['labels']):
                    w.writerow([lb, ch['values'][i]])
                if ch['kind'] == 'bars2':
                    w.writerow(['در انتظار', ''])
                    for i, lb in enumerate(ch['labels']):
                        w.writerow([lb, ch['values2'][i]])
            elif ch['kind'] == 'line':
                w.writerow(['ماه'] + [s['name'] for s in ch['series']])
                for i, m in enumerate(ch['labels']):
                    w.writerow([m] + [s['values'][i] for s in ch['series']])
            return '\ufeff' + buf.getvalue()
    if cid == 'budgets' and data.get('budget_table'):
        t = data['budget_table']
        buf = io.StringIO()
        w = _csv.writer(buf, lineterminator='\r\n')
        w.writerow(t['headers'])
        w.writerows(t['rows'])
        return '\ufeff' + buf.getvalue()
    return None

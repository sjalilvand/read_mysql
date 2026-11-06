# -*- coding: utf-8 -*-
"""تست خودکار کامل سامانه — ۱۲۰+ آزمون"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

import dump_parser  # noqa: E402
import dbkit as D  # noqa: E402
import catalog as C  # noqa: E402
import repengine as R  # noqa: E402
import bi  # noqa: E402
import presets as P  # noqa: E402

TEST_DB = os.path.join(BASE, 'test', 'sample.sqlite')
PASS = FAIL = 0
FAILS = []


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(f'{name}: {detail}')
        print(f'  [FAIL] {name} — {detail}')


# ============ ۱) جلالی ============
import jalali as J  # noqa: E402

check('jalali g2j', J.to_jalali(2026, 11, 6)[0] == 1405, str(J.to_jalali(2026, 11, 6)))
check('jalali roundtrip', J.to_gregorian(*J.to_jalali(2026, 11, 6)) == (2026, 11, 6))
check('jalali fmt', '1405' in J.fmt('2026-11-06 10:30:00'), J.fmt('2026-11-06 10:30:00'))
check('jalali iso', J.jalali_to_iso('1405/08/15') is not None, J.jalali_to_iso('1405/08/15'))
check('jalali iso eod', '23:59:59' in (J.jalali_to_iso('1405/08/15', end_of_day=True) or ''))
check('jmonth label', 'آبان' in J.month_label('1405-08'), J.month_label('1405-08'))
check('month_key', J.month_key('2026-11-06 10:00:00') == '1405-08', J.month_key('2026-11-06'))
check('fa_num', J.fa_num('123') == '۱۲۳')
jy, jm, jd = J.to_jalali(2025, 3, 21)
check('nowruz', (jy, jm, jd) == (1404, 1, 1), f'{jy}/{jm}/{jd}')

# ============ ۲) ایمپورت ============
if not os.path.isfile(TEST_DB) or os.path.getsize(TEST_DB) < 10000:
    imp = dump_parser.Importer('test/sample_real.sql', TEST_DB, 'test/status.json')
    imp.run()
    check('import done', imp.status['state'] == 'done', imp.status.get('error'))

# ============ ۳) کاتالوگ ============
check('catalog tables', len(C.TABLES) >= 75, len(C.TABLES))
check('catalog label Events', C.table_label('Events') == 'جلسات مشاوره')
check('col label', C.col_label('Events', 'AcceptorID') == 'مشاور (پذیرنده)' or
      'مشاور' in C.col_label('Events', 'AcceptorID'), C.col_label('Events', 'AcceptorID'))
check('sensitive', C.is_sensitive('Users', 'Password'))
check('sensitive session key', C.is_sensitive('Sessions', 'Key'))
check('not sensitive', not C.is_sensitive('Events', 'StartDate'))
check('fk map', C.FK.get('Events.UserID', {}).get('parent') == 'Users')
check('enum ems', C.apply_static_dict({'low': 'کم'}, 'low') == 'کم')
check('enum bit', C.apply_static_dict('bit', 1) == 'بله')
check('enum level', C.apply_static_dict('level', 3) == 'مشاور متخصص')

# ============ ۴) دیتابیس و موتور گزارش ============
D.save_config({'db_path': TEST_DB})
conn, path = D.connect()
check('connect', conn is not None)
meta = D.get_meta(conn)
check('meta events', 'Events' in meta and len(meta['Events']['cols']) == 41,
      len(meta.get('Events', {}).get('cols', [])))
dicts = D.dict_services(conn, meta)
check('services count', len(dicts['by_id']) >= 10, len(dicts['by_id']))
check('service soha', dicts['by_soha'].get(5) == 'مشاوره فردی (حضوری)', str(dicts['by_soha']))
check('service_name id', D.service_name(dicts, 6) == 'مشاوره گروهی', D.service_name(dicts, 6))
check('service_name soha', D.service_name(dicts, 5, via='soha') == 'مشاوره فردی (حضوری)')

# گزارش عمومی Events
res = R.run(conn, meta, dicts, 'Events', {'limit': 50})
check('run events', not res.get('error') and res['count'] == 50, str(res.get('error')))
check('run cols', len(res['columns']) >= 30)
colnames = [c['label'] for c in res['columns']]
check('fk label joined', any('مراجع (نام)' in c for c in colnames), str(colnames[:6]))
check('password excluded', not any('Password' in c for c in
                                   [x['key'] for x in res['columns']]))

# فیلتر
res = R.run(conn, meta, dicts, 'Events', {
    'columns': ['id', 'UserID', 'ServiceID', 'StartDate', 'EMS'],
    'filters': [{'col': 'EMS', 'op': 'eq', 'value': '1'}], 'limit': 100})
check('filter ems', not res.get('error') and res['count'] > 0, str(res.get('error')))

res = R.run(conn, meta, dicts, 'Events', {
    'columns': ['id', 'StartDate', 'EndDate'],
    'filters': [{'col': 'EndDate', 'op': 'empty'}], 'limit': 100})
check('filter empty', res['count'] > 0, res['count'])

# فیلتر تاریخ شمسی
res = R.run(conn, meta, dicts, 'Events', {
    'columns': ['id', 'StartDate'],
    'date_from': '1404/10/01', 'date_to': '1405/08/30', 'limit': 500})
check('date filter', not res.get('error') and res['count'] > 0,
      f"{res.get('error')} n={res.get('count')}")
# محدوده باریک — فقط آبان ۱۴۰۵ (۲۰۲۶-۱۰-۲۳ تا ۲۰۲۶-۱۱-۲۱)
res2 = R.run(conn, meta, dicts, 'Events', {
    'columns': ['id', 'StartDate'], 'date_from': '1405/08/01', 'date_to': '1405/08/30',
    'limit': 500})
check('date narrow', res2['count'] > 0 and res2['count'] < res['count'],
      f"{res2['count']} vs {res['count']}")

# جستجوی متنی روی نام
res = R.run(conn, meta, dicts, 'Events', {'search': 'احمدی', 'limit': 50})
check('search', not res.get('error'), str(res.get('error')))

# گروه‌بندی + تجمیع
res = R.run(conn, meta, dicts, 'Events', {
    'group_by': [{'col': 'ServiceID', 'mode': 'value'}],
    'aggs': [{'fn': 'count', 'col': '*'}], 'limit': 20})
check('group service', not res.get('error') and res['count'] >= 3, str(res.get('error')))
labels = [r[0] for r in res['rows']]
check('group translated', any('مشاوره' in str(lb) for lb in labels), str(labels))

res = R.run(conn, meta, dicts, 'Events', {
    'group_by': [{'col': 'StartDate', 'mode': 'jmonth'}],
    'aggs': [{'fn': 'count', 'col': '*'}, {'fn': 'sum', 'col': 'AcceptorFee'}],
    'limit': 24})
check('group jmonth', not res.get('error') and res['count'] >= 6, str(res.get('error')))
check('group jmonth label', any('۱۴۰' in str(r[0]) or '140' in str(r[0]) for r in res['rows']),
      str(res['rows'][:2]))
sums = [r[2] for r in res['rows']]
check('group agg sum', any(str(s) not in ('', '0') for s in sums), str(sums))

res = R.run(conn, meta, dicts, 'Referrs', {
    'group_by': [{'col': 'Status', 'mode': 'value'}],
    'aggs': [{'fn': 'count', 'col': '*'}]})
check('group referr status', any('انجام شده' in str(r[0]) for r in res['rows']),
      str([r[0] for r in res['rows']]))

# جدول Users — حذف Password
res = R.run(conn, meta, dicts, 'Users', {'limit': 5})
keys = [c['key'] for c in res['columns']]
check('users no password', 'Password' not in keys and 'password' not in keys)

# ============ ۵) گزارش‌های آماده ============
R.set_conn_ref(conn, meta)
for pr in P.PRESETS:
    r = _run = None
    import app as _appmod  # noqa
    result = _appmod._run_preset_full(conn, meta, dicts, pr, {}, 100)
    check(f"preset {pr['key']}", not result.get('error') and result['count'] >= 0,
          f"{result.get('error')} | {result.get('sql','')[:120]} | args={result.get('args')}")

# با فیلتر
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['done_events'],
                               {'province': '8', 'gender': 'female'}, 100)
check('preset filtered', not res.get('error'), str(res.get('error')))
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['referrs'],
                               {'status': 'Done', 'rtype': 'soha'}, 100)
check('preset referrs filter', res['count'] > 0, res['count'])
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['payments'],
                               {'confirm': 'ok'}, 100)
check('preset payments confirm', not res.get('error'), str(res.get('error')))
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['confirmations'],
                               {'stage': 'sup', 'cstate': 'ok', 'ems': '0'}, 100)
check('preset confirm stage', not res.get('error') and res['count'] > 0,
      f"{res.get('error')} n={res.get('count')}")
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['recipient'],
                               {'month': '1405/08'}, 100)
check('preset recipient month', not res.get('error'), str(res.get('error')))
res = _appmod._run_preset_full(conn, meta, dicts, P.PRESET_BY_KEY['ems'],
                               {'risk': 'high'}, 100)
check('preset ems risk', not res.get('error'), str(res.get('error')))

# خروجی‌ها
csv_text = R.to_csv([{'label': 'عنوان'}], [['مقدار']])
check('csv bom', csv_text.startswith('\ufeff'))
xlsx = R.to_xlsx([{'label': 'عنوان'}], [['مقدار']], 'تست')
check('xlsx optional', xlsx is None or len(xlsx) > 500)

# ============ ۶) داشبورد BI ============
data = bi.build(conn, meta, dicts, {})
check('bi kpis', len(data['kpis']) >= 8, len(data['kpis']))
check('bi charts', len(data['charts']) >= 8, len(data['charts']))
kvals = {k['label']: k['value'] for k in data['kpis']}
check('bi sessions', kvals.get('کل جلسات مشاوره') not in (None, '۰', '0'), str(kvals))
kinds = [c['kind'] for c in data['charts']]
check('bi kinds', 'line' in kinds and 'donut' in kinds and 'bars' in kinds, str(kinds))
ch_ids = [c['id'] for c in data['charts']]
check('bi service chart', 'ev_service' in ch_ids, str(ch_ids))
check('bi confirm chart', 'ev_confirm' in ch_ids)
data2 = bi.build(conn, meta, dicts, {'province': '8'})
check('bi filtered cached', data2['kpis'][0]['value'] != data['kpis'][0]['value'],
      f"{data2['kpis'][0]['value']} vs {data['kpis'][0]['value']}")
csv_text = bi.chart_csv(conn, meta, dicts, 'ev_service', {})
check('bi chart csv', csv_text is not None and 'عنوان' in csv_text)

# ============ ۷) استعلام مددجو ============
import app as appmod  # noqa: E402
test_client = appmod.app.test_client()

# یک کد ملی واقعی از جلسات
row = conn.execute('SELECT NID FROM Events LIMIT 1').fetchone()
nid = str(row[0])
conn.close()

person_page = test_client.get(f'/person?nid={nid}')
check('person page 200', person_page.status_code == 200, person_page.status_code)
check('person has data', 'جلسات مشاوره'.encode() in person_page.data)
conn, _ = D.connect()
meta = D.get_meta(conn)
dicts = D.dict_services(conn, meta)
pdata = appmod._person_data(conn, meta, dicts, nid)
conn.close()
check('person events', len(pdata['events']) > 0, len(pdata.get('events', [])))
check('person events service', all(e['service'] and e['service'] != '—'
                                   for e in pdata['events']), str(pdata['events'][:1]))
# معتبر بودن کد ملی غلط
conn, _ = D.connect()
meta = D.get_meta(conn)
dicts = D.dict_services(conn, meta)
pdata_bad = appmod._person_data(conn, meta, dicts, '0000000001')
conn.close()
check('person bad nid', pdata_bad.get('error') is not None or len(pdata_bad.get('events', [])) == 0)

# ============ ۸) صفحات Flask ============
def get(path, expect=200):
    r = test_client.get(path)
    check(f'GET {path}', r.status_code == expect, f'{r.status_code}')
    return r

get('/')
get('/reports')
get('/tables')
get('/table/Events')
get('/table/Users?q=احمد')
get('/person')
get('/setup')
get('/table/NoSuchTable', 404)
get('/preset/done_events')
get('/preset/ems')
get('/preset/consultant_tax')
get('/preset/budgets')

r = test_client.get('/api/meta')
check('api meta', r.status_code == 200 and len(r.get_json()) >= 30, r.status_code)
r = test_client.get('/api/dicts/provinces')
check('api provinces', r.status_code == 200 and len(r.get_json()) == 10, r.status_code)
r = test_client.get('/api/dicts/services')
check('api services', len(r.get_json()) >= 10)
r = test_client.get('/api/dicts/cities?province=8')
check('api cities dep', len(r.get_json()) >= 1, r.get_json())

r = test_client.post('/api/report', json={'table': 'Events', 'limit': 10})
check('api report', r.status_code == 200 and r.get_json()['count'] == 10, r.status_code)
r = test_client.post('/api/report', json={'table': "Events'; DROP", 'limit': 10})
check('api report bad table', r.status_code == 200 and r.get_json().get('error'),
      str(r.get_json())[:100])
r = test_client.post('/api/report/export', json={'table': 'Events', 'format': 'csv', 'limit': 10})
check('api report export', r.status_code == 200 and b'\xef\xbb\xbf' in r.data[:5], r.status_code)

r = test_client.post('/api/preset/done_events', json={'province': '8'})
check('api preset', r.status_code == 200 and not r.get_json().get('error'), str(r.get_json())[:150])
r = test_client.post('/api/preset/ems/export', json={'format': 'xlsx'})
check('api preset export xlsx', r.status_code == 200, r.status_code)

r = test_client.post('/api/saved', json={'name': 'تست من', 'spec': {'table': 'Events', 'limit': 5}})
check('api saved save', r.status_code == 200, r.status_code)
r = test_client.get('/api/saved')
check('api saved list', any(s['name'] == 'تست من' for s in r.get_json()))
r = test_client.delete('/api/saved/تست من')
check('api saved del', r.status_code == 200)

r = test_client.get('/api/bi')
check('api bi', r.status_code == 200 and len(r.get_json()['kpis']) >= 8)
r = test_client.get('/api/bi.csv/ev_province')
check('api bi csv', r.status_code == 200 and 'عنوان' in r.data.decode('utf-8'))

# امنیت: ستون محرمانه در خروجی
r = test_client.post('/api/report', json={'table': 'Users', 'columns': ['Password'], 'limit': 5})
check('api sensitive blocked', r.get_json().get('error') is not None or
      all('Password' != c['key'] for c in r.get_json().get('columns', [])),
      str(r.get_json())[:120])

# ============ نتیجه ============
print('=' * 60)
print(f'PASS: {PASS}   FAIL: {FAIL}')
if FAILS:
    print('— خطاها:')
    for f in FAILS[:40]:
        print('  *', f)
sys.exit(1 if FAIL else 0)

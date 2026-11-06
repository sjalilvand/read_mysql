# -*- coding: utf-8 -*-
"""لایه دسترسی داده: مدیریت منبع داده (بکاپ یا دیتابیس آماده)، متادیتا و
دیکشنری‌های دینامیک (خدمات، نقش‌ها، استان‌ها...) خوانده‌شده از خود دیتابیس.
"""

import json
import os
import sqlite3
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'config.json')
OWN_DB = os.path.join(BASE_DIR, 'data', 'app.sqlite')
STATUS_PATH = os.path.join(BASE_DIR, 'data', 'import_status.json')

DEFAULT_SQL_CANDIDATES = [
    r'D:\Projects\sql_viewer\app2_backup_202611031659.sql',
    r'D:\Projects\sql_viewer\app2_backup.sql',
]
EXTERNAL_DB_CANDIDATES = [
    r'D:\Projects\sql_viewer\viewer_data\parsed.sqlite',
    os.path.join(os.path.dirname(BASE_DIR), 'sql_viewer', 'viewer_data', 'parsed.sqlite'),
]
SQL_DIRS = [os.path.join(BASE_DIR, 'backups'), BASE_DIR,
            r'D:\Projects\sql_viewer']

_lock = threading.Lock()
_meta_cache = {'ts': 0, 'data': None}
_dict_cache = {}


# ---------------- پیکربندی ----------------

def load_config():
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    tmp = CONFIG_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    try:
        os.replace(tmp, CONFIG_PATH)
    except OSError:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    _meta_cache['data'] = None
    _dict_cache.clear()


def active_db_path():
    """مسیر دیتابیس SQLite فعال؛ None یعنی منبعی تنظیم نشده"""
    cfg = load_config()
    p = cfg.get('db_path')
    if p and os.path.isfile(p):
        return p
    if os.path.isfile(OWN_DB) and os.path.getsize(OWN_DB) > 4096:
        return OWN_DB
    return None


def db_writable(path):
    try:
        conn = sqlite3.connect(path)
        conn.execute('SELECT 1')
        conn.close()
        return True
    except sqlite3.Error:
        return False


# ---------------- اتصال ----------------

def connect(readonly=True):
    p = active_db_path()
    if not p:
        return None, None
    try:
        if readonly:
            conn = sqlite3.connect(f'file:{p}?mode=ro', uri=True, timeout=20)
        else:
            conn = sqlite3.connect(p, timeout=20)
        conn.execute('PRAGMA cache_size=-32768')
        conn.execute('PRAGMA temp_store=MEMORY')
    except sqlite3.Error:
        return None, None
    return conn, p


# ---------------- متادیتا ----------------

def get_meta(conn, force=False):
    """{logical_name: {sname, kind, cols: [names], coltypes: {name: stype}, rows: int}}"""
    with _lock:
        if not force and _meta_cache['data'] is not None:
            return _meta_cache['data']
    meta = {}
    try:
        rows = conn.execute(
            'SELECT name, sname, kind, columns, rows FROM _meta').fetchall()
    except sqlite3.Error:
        rows = []
    for name, sname, kind, cols_json, n in rows:
        cols, types = [], {}
        try:
            parsed = json.loads(cols_json or '[]')
            for c in parsed:
                cols.append(c.get('name'))
                types[c.get('name')] = (c.get('stype') or 'TEXT').upper()
        except Exception:
            pass
        meta[name] = {'sname': sname, 'kind': kind or 'table', 'cols': cols,
                      'types': types, 'rows': n or 0}
    # جدول‌های واقعی که در _meta نیستند (احتمال نادر)
    try:
        for (nm,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name != '_meta'"):
            if not any(m['sname'] == nm for m in meta.values()):
                meta[nm] = {'sname': nm, 'kind': 'table', 'cols': [], 'types': {}, 'rows': 0}
    except sqlite3.Error:
        pass
    with _lock:
        _meta_cache['ts'] = time.time()
        _meta_cache['data'] = meta
    return meta


def sname(meta, table):
    info = meta.get(table)
    return info['sname'] if info else table


def col_type(meta, table, col):
    info = meta.get(table) or {}
    t = (info.get('types') or {}).get(col, 'TEXT')
    return t or 'TEXT'


def table_rows(meta, table):
    info = meta.get(table) or {}
    return info.get('rows') or 0


# ---------------- دیکشنری‌های دینامیک ----------------

def _run(conn, sql):
    try:
        return conn.execute(sql).fetchall()
    except sqlite3.Error:
        return []


def dict_services(conn, meta):
    """{'by_id': {id: name}, 'by_soha': {sohaid: name}, 'weights': {id: weight}}"""
    out = _dict_cache.get('services')
    if out is not None:
        return out
    by_id, by_soha, weights = {}, {}, {}
    sn = sname(meta, 'Services')
    for i, nm, sh, w in _run(conn,
            f'SELECT id, Name, Short, Weight FROM "{sn}" ORDER BY id'):
        label = f'{nm}' if not sh or sh == nm else f'{nm}'
        by_id[i] = nm or str(i)
        if w is not None:
            weights[i] = w
        if sh and sh not in by_soha:
            by_soha[sh] = nm or str(i)
    # نگاشت SohaID همیشه بر اساس ستون SohaID
    by_soha = {}
    for i, nm, soha, w in _run(conn,
            f'SELECT id, Name, SohaID, Weight FROM "{sn}" ORDER BY id'):
        if soha is not None:
            by_soha[soha] = nm or str(i)
    out = {'by_id': by_id, 'by_soha': by_soha, 'weights': weights}
    _dict_cache['services'] = out
    return out


def service_name(dicts, value, via=None):
    """نام خدمت برای مقدار عددی — با ترجیح مسیر via ('id' یا 'soha')"""
    if value in (None, '', '0'):
        return None
    try:
        v = int(value)
    except (ValueError, TypeError):
        return str(value)
    order = []
    if via == 'soha':
        order = ['by_soha', 'by_id']
    elif via == 'id':
        order = ['by_id', 'by_soha']
    else:
        order = ['by_id', 'by_soha']
    for k in order:
        nm = dicts.get(k, {}).get(v)
        if nm:
            return nm
    return f'خدمت {v}'


def dict_simple(conn, meta, table, label_col='Name'):
    """{id: label} برای جدول‌های ساده"""
    key = f'simple:{table}:{label_col}'
    out = _dict_cache.get(key)
    if out is not None:
        return out
    sn = sname(meta, table)
    info = meta.get(table)
    pk = 'id'
    if info and info['cols']:
        pk = info['cols'][0]
    out = {r[0]: r[1] for r in _run(
        conn, f'SELECT "{pk}", "{label_col}" FROM "{sn}" ORDER BY "{pk}"') if r[0] is not None}
    _dict_cache[key] = out
    return out


def dict_provinces(conn, meta):
    return dict_simple(conn, meta, 'Provinces', 'Title')


def dict_centers(conn, meta):
    key = 'centers'
    out = _dict_cache.get(key)
    if out is not None:
        return out
    sn = sname(meta, 'Centers')
    out = {r[0]: r[1] for r in _run(
        conn, f'SELECT id, CenterTitle FROM "{sn}" ORDER BY CenterTitle') if r[0] is not None}
    _dict_cache[key] = out
    return out


def dict_cities(conn, meta):
    key = 'cities'
    out = _dict_cache.get(key)
    if out is not None:
        return out
    sn = sname(meta, 'Cities')
    out = {r[0]: r[1] for r in _run(
        conn, f'SELECT id, Title FROM "{sn}" ORDER BY Title') if r[0] is not None}
    _dict_cache[key] = out
    return out


def dict_cities_by_province(conn, meta):
    key = 'cities_by_province'
    out = _dict_cache.get(key)
    if out is not None:
        return out
    sn = sname(meta, 'Cities')
    out = {}
    for pid, cid, title in _run(
            conn, f'SELECT ProvinceID, id, Title FROM "{sn}" ORDER BY Title'):
        out.setdefault(pid, []).append({'id': cid, 'title': title})
    _dict_cache[key] = out
    return out


def dict_roles(conn, meta):
    return dict_simple(conn, meta, 'Roles', 'Title')


def dict_users_counts(meta):
    return table_rows(meta, 'Users')


def clear_dict_cache():
    _dict_cache.clear()


# ---------------- کشف منابع ----------------

def discover_sources():
    """فهرست منابع داده قابل انتخاب: فایل‌های .sql و دیتابیس‌های آماده"""
    sqls, dbs, seen = [], [], set()

    def add(kind, path, note=''):
        rp = os.path.abspath(path)
        if rp in seen or not os.path.isfile(rp):
            return
        seen.add(rp)
        try:
            size = os.path.getsize(rp)
        except OSError:
            return
        if kind == 'sql' and size < 1024:
            return
        if kind == 'db':
            try:
                with open(rp, 'rb') as fh:
                    if fh.read(16)[:15] != b'SQLite format 3':
                        return
            except OSError:
                return
        target = sqls if kind == 'sql' else dbs
        target.append(
            {'kind': kind, 'path': rp, 'size': size, 'note': note})

    for p in DEFAULT_SQL_CANDIDATES:
        add('sql', p, 'مسیر پیش‌فرض پروژه')
    for d in SQL_DIRS:
        if not os.path.isdir(d):
            continue
        try:
            for fn in os.listdir(d):
                if fn.lower().endswith('.sql'):
                    add('sql', os.path.join(d, fn))
        except OSError:
            pass
    for p in EXTERNAL_DB_CANDIDATES:
        add('db', p, 'استخراج‌شده توسط sql_viewer — بدون نیاز به ایمپورت')
    add('db', OWN_DB, 'دیتابیس خود برنامه')
    # داده نمونه همراه برنامه (برای آشنایی با امکانات قبل از ایمپورت بکاپ واقعی)
    sample = os.path.join(BASE_DIR, 'test', 'sample_real.sql')
    if os.path.isfile(sample):
        add('sql', sample, 'داده نمونه — برای آشنایی با برنامه')
    return {'sql': sqls, 'db': dbs}

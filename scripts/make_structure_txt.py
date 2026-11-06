# -*- coding: utf-8 -*-
"""تولید database_structure.txt — ساختار کامل دیتابیس برای هوش مصنوعی
منابع: catalog.py (برچسب/توضیح فارسی + کلیدهای خارجی) + CREATE TABLEهای نمونه واقعی
+ شمارش ردیف‌های واقعی دیتابیس تولیدی (ارسالی کاربر).
"""

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import catalog as C  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# شمارش ردیف‌های واقعی دیتابیس (از فهرست ارسالی کاربر — دیتابیس کامل ۱٫۲۸ گیگابایتی)
REAL_ROWS = {
    'Log': 1567061, 'ApiReports': 806544, 'EventComments': 579200, 'Events': 549848,
    'EventPersonal': 524790, 'SMS': 452175, 'Referrs': 362410, 'Users': 320471,
    'EventReserves': 315056, '_fix_endrefer': 137981, 'GroupEventMember': 53746,
    'Sessions': 52094, 'GroupMembers': 46202, 'EventPsychology': 24874,
    'EventReferrs': 22364, 'ConsultantCourses': 14009, 'JobsList': 12380,
    'EventQuizzes': 8740, 'EventDisorders': 8299, 'Groups': 6415, 'GroupEvents': 6364,
    'EventsEms': 5202, 'ConsultantTax': 4887, 'UserRoles': 3030,
    'ConsultantExperience': 2112, 'ConsultantTeachingExperience': 2061,
    'ReferrsRequest': 1878, 'ReferrFollowUps': 1731, 'EventNeuroFeedback': 1341,
    'Files': 1264, 'ConsultantEducation': 1252, 'CenterBankAccount': 1204,
    'Cities': 1121, 'CareerCounseling': 1056, 'Centers': 902,
    'EventChildPsychology': 711, 'EventEmsComments': 702, 'ConsultantHistory': 666,
    'Disorders': 513, 'BudgetCity': 488, 'ApiStates': 438, 'Messages': 298,
    'EventMedicine': 217, 'EventHeadMap': 178, 'BudgetProvince': 165,
    'CorporateContractServices': 139, 'UserMFA': 103, 'BudgetCenter': 69,
    'CorporateContractCoupons': 55, 'CenterEquipments': 39, 'Provinces': 31,
    'Settings': 24, 'CorporateContracts': 22, 'Roles': 21, 'Services': 15,
    'EquipmentItems': 13, 'Education': 9, 'Budget': 6, 'CorporateCustomers': 6,
    'Marriage': 6, 'Religion': 6, 'CenterCategories': 5, 'SpecialOccasions': 4,
    'InvitePersons': 3, 'ApiTokens': 1, 'CorporateContractNIDs': 1,
    'UserTicket': 1, 'ConsultScope': 0, 'Expenses': 0, 'GroupEventReserves': 0,
    'Helps': 0, 'Incomes': 0, 'Notifications': 0, 'NotificationsQueue': 0,
    'UserPasskeys': 0,
}


_COLTYPE_RE = re.compile(
    r'`(\w+)`\s+((?:int|bigint|smallint|tinyint|mediumint|varchar|char|text|longtext|'
    r'mediumtext|datetime|date|timestamp|decimal|double|float|bit|json|blob|time)\b'
    r'(?:\([^)]*\))?)([^,]*)', re.I)


def parse_create_tables(path):
    """استخراج ستون‌ها و نوع‌ها از CREATE TABLEهای فایل SQL (تک‌خطی یا چندخطی)"""
    out = {}
    try:
        with io.open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return out
    for m in re.finditer(r'CREATE TABLE\s+`?(\w+)`?\s*\((.*?)\)\s*(?:ENGINE|;)', text,
                         re.S | re.I):
        tname, body = m.group(1), m.group(2)
        cols = []
        for cm in _COLTYPE_RE.finditer(body):
            cname, ctype, tail = cm.group(1), cm.group(2), cm.group(3) or ''
            note = ' NOT NULL' if re.search(r'NOT NULL', tail, re.I) else ''
            if re.search(r'AUTO_INCREMENT', tail, re.I):
                note += ' AUTO_INCREMENT'
            cols.append((cm.group(1), cm.group(2) + note))
        if cols:
            out[tname] = cols
    return out


def main():
    sample = os.path.join(BASE, 'test', 'sample_real.sql')
    schemas = parse_create_tables(sample)
    names = sorted(set(list(REAL_ROWS) + list(C.TABLES) + list(schemas)))
    names = [n for n in names if not n.startswith('sqlite_')]

    total_rows = sum(REAL_ROWS.values())
    L = []
    ap = L.append
    ap('ساختار کامل دیتابیس — سامانه مراکز خدمات روانشناسی و مشاوره «راه زندگی»')
    ap('استخراج‌شده از بکاپ MySQL واقعی (app2_backup) — برای تحلیل توسط هوش مصنوعی')
    ap('=' * 100)
    ap(f'تعداد جدول‌ها: {len(names)}   |   مجموع ردیف‌ها: {total_rows:,}')
    ap(f'سرویس خارجی مرتبط: سامانه سها (ارجاع، نوبت‌دهی و پرداخت وزارت بهداشت)')
    ap('نکته: ایندکس‌ها و کلیدهای خارجی سطح MySQL در بکاپ وجود دارد؛ روابط منطقی ستون «رابطه» هر ستون آمده است.')
    ap('')
    ap('فهرست کلی جدول‌ها (مرتب بر اساس حجم داده):')
    ap('-' * 100)
    header = f'{"جدول":<32}{"نام فارسی":<28}{"ردیف‌ها":>12}  {"ستون‌ها":>7}  توضیح'
    ap(header)
    ap('-' * 100)
    ordered = sorted(names, key=lambda n: -REAL_ROWS.get(n, 0))
    for n in ordered:
        lbl, desc = C.TABLES.get(n, (n, ''))
        ap(f'{n:<32}{lbl:<28}{REAL_ROWS.get(n, 0):>12,}  {len(schemas.get(n, [])):>7}  {desc}')
    ap('')

    ap('=' * 100)
    ap('جزئیات هر جدول (ستون‌ها، نوع داده و روابط):')
    ap('=' * 100)
    for n in ordered:
        lbl, desc = C.TABLES.get(n, (n, ''))
        ap('')
        ap(f'■ {n} — {lbl}')
        ap(f'  توضیح: {desc or "—"}')
        ap(f'  ردیف‌ها: {REAL_ROWS.get(n, 0):,}')
        pdate = C.PRIMARY_DATE.get(n)
        if pdate:
            ap(f'  ستون تاریخ اصلی: {pdate}')
        cols = schemas.get(n)
        if not cols:
            ap('  ستون‌ها: (در نمونه موجود نیست — از متادیتای برنامه در زمان اجرا خوانده می‌شود)')
            continue
        ap('  ستون‌ها:')
        for cname, ctype in cols:
            fk = C.FK.get(f'{n}.{cname}')
            rel = ''
            if fk:
                rel = f'  → FK به {fk["parent"]}'
            lab = ''
            try:
                cl = C.col_label(n, cname)
                if cl and cl != cname:
                    lab = f' ({cl})'
            except Exception:
                pass
            sens = '  [حساس — پنهان‌سازی]' if C.is_sensitive(n, cname) else ''
            ap(f'    - {cname:<28}{ctype:<22}{lab}{rel}{sens}')
    ap('')
    ap('پایان فایل ساختار — این فایل به‌روزرسانی‌شده بر اساس بکاپ واقعی است.')

    out = os.path.join(BASE, 'database_structure.txt')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print('written:', out, f'({os.path.getsize(out):,} bytes, {len(L)} lines)')


if __name__ == '__main__':
    main()

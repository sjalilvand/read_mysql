# -*- coding: utf-8 -*-
"""ابزارهای تاریخ شمسی (جلالی) و ارقام فارسی — سمت سرور، بدون وابستگی.

الگوریتم تبدیل بر پایه الگوریتم عمومی jalaali (همان الگوریتم jalali.js سمت کلاینت)
تا خروجی سرور و کلاینت همیشه یکسان باشد.
"""

import re

BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
          1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178]

MONTH_NAMES = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
               'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

WEEKDAYS = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']

FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def fa_num(v):
    """تبدیل رقم‌های لاتین یک عدد/رشته به فارسی"""
    return str(v).translate(FA_DIGITS)


def _div(a, b):
    """تقسیم صحیح با گرد شدن به سمت صفر (مطابق الگوریتم مرجع JS)"""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        return -q
    return q


def _mod(a, b):
    return a - _div(a, b) * b


def _jal_cal(jy):
    bl = len(BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    jm = jump = leap = 0
    for i in range(1, bl):
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm
    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march


def _g2d(gy, gm, gd):
    d = _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4) \
        + _div(153 * _mod(gm + 9, 12) + 2, 5) + gd - 34840408
    d = d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
    return d


def _d2g(jdn):
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(_mod(j, 1461), 4) * 5 + 308
    gd = _div(_mod(i, 153), 5) + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def _j2d(jy, jm, jd):
    r = _jal_cal(jy)
    return _g2d(r[1], 3, r[2]) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2j(jdn):
    gy = _d2g(jdn)[0]
    jy = gy - 621
    r = _jal_cal(jy)
    jdn1f = _g2d(gy, 3, r[2])
    jd = jdn - jdn1f
    if jd >= 0:
        if jd <= 185:
            jm = 1 + _div(jd, 31)
            jdm = _mod(jd, 31) + 1
            return jy, jm, jdm
        jd -= 186
    else:
        jy -= 1
        jd += 179
        if r[0] == 1:
            jd += 1
    jm = 7 + _div(jd, 30)
    jdm = _mod(jd, 30) + 1
    return jy, jm, jdm


def to_jalali(gy, gm, gd):
    """میلادی → جلالی"""
    return _d2j(_g2d(gy, gm, gd))


def to_gregorian(jy, jm, jd):
    """جلالی → میلادی"""
    return _d2g(_j2d(jy, jm, jd))


_DT_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[T ]?(\d{2}):(\d{2})(?::(\d{2}))?')
_D_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
_YM_RE = re.compile(r'^(\d{4})-(\d{1,2})$')
_JIN_RE = re.compile(r'^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$')


def fmt(value, with_time=True, with_weekday=False):
    """نمایش مقدار تاریخ/زمان (ISO) به شمسی خوانا؛ ورودی نامعتبر → همان رشته"""
    if value is None or value == '':
        return ''
    s = str(value).strip()
    m = _DT_RE.match(s)
    if m:
        gy, gm, gd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm = m.group(4), m.group(5)
        try:
            jy, jm, jd = to_jalali(gy, gm, gd)
        except Exception:
            return s
        out = f'{jy}/{jm:02d}/{jd:02d}'
        if with_weekday:
            wd = WEEKDAYS[_j2d(jy, jm, jd) % 7]
            out = f'{wd} {out}'
        if with_time and (hh != '00' or mm != '00'):
            out += ' — ' + fa_num(f'{hh}:{mm}')
        return out
    m = _D_RE.match(s)
    if m:
        try:
            jy, jm, jd = to_jalali(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return s
        return f'{jy}/{jm:02d}/{jd:02d}'
    return s


def month_key(value):
    """کلید ماه شمسی به شکل '1404-07' برای گروه‌بندی؛ ورودی: تاریخ کامل یا 'YYYY-MM'"""
    s = str(value or '').strip()
    m = _YM_RE.match(s)
    if m:
        try:
            jy, jm, jd = to_jalali(int(m.group(1)), int(m.group(2)), 15)
        except Exception:
            return None
        return f'{jy}-{jm:02d}'
    m = _DT_RE.match(s) or _D_RE.match(s)
    if not m:
        return None
    try:
        jy, jm, jd = to_jalali(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None
    return f'{jy}-{jm:02d}'


def month_label(key):
    """'1404-07' → 'مهر ۱۴۰۴'"""
    if not key:
        return ''
    try:
        y, mth = key.split('-')
        y, mth = int(y), int(mth)
    except ValueError:
        return key
    return f'{MONTH_NAMES[mth - 1]} {fa_num(y)}'


def jalali_to_iso(text, end_of_day=False):
    """'1404/07/12' (یا با - یا .) → '2025-10-04'؛ با end_of_day ساعت 23:59:59"""
    if not text:
        return None
    s = str(text).strip().replace('۰', '0').replace('۱', '1').replace('۲', '2') \
        .replace('۳', '3').replace('۴', '4').replace('۵', '5').replace('۶', '6') \
        .replace('۷', '7').replace('۸', '8').replace('۹', '9')
    m = _JIN_RE.match(s)
    if not m:
        # شاید خودش ISO باشد
        if _D_RE.match(s):
            return s
        return None
    jy, jm, jd = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        gy, gm, gd = to_gregorian(jy, jm, jd)
    except Exception:
        return None
    if end_of_day:
        return f'{gy:04d}-{gm:02d}-{gd:02d} 23:59:59'
    return f'{gy:04d}-{gm:02d}-{gd:02d}'


def today_jalali():
    import datetime
    t = datetime.date.today()
    jy, jm, jd = to_jalali(t.year, t.month, t.day)
    return f'{jy}/{jm:02d}/{jd:02d}'


def month_range_keys(rows_idx):
    """مرتب‌سازی کلیدهای ماه شمسی"""
    return sorted(k for k in rows_idx if k)

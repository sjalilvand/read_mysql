# -*- coding: utf-8 -*-
"""گزارش‌های آماده — بازسازی دقیق صفحات گزارش برنامه اصلی «راه زندگی».

هر گزارش: SQL پایه + فیلترهای همان صفحه اصلی + ستون‌های همان جدول اصلی.
مقادیر {where} در SQL جای فیلترهای فعال می‌نشیند (پارامتری و امن).
"""

import jalali as J


# ---------- تبدیل‌های ویژه ----------

def _jmonth_start(v):
    """'1404/07' → ابتدای ماه شمسی به ISO"""
    try:
        parts = str(v).replace('-', '/').split('/')
        jy, jm = int(parts[0]), int(parts[1])
        return J.jalali_to_iso(f'{jy}/{jm:02d}/01')
    except Exception:
        return None


def _jmonth_end(v):
    try:
        parts = str(v).replace('-', '/').split('/')
        jy, jm = int(parts[0]), int(parts[1])
        ny, nm = (jy + 1, 1) if jm == 12 else (jy, jm + 1)
        nxt = J.to_gregorian(ny, nm, 1)
        import datetime
        d = datetime.date(nxt[0], nxt[1], nxt[2]) - datetime.timedelta(days=1)
        return f'{d.isoformat()} 23:59:59'
    except Exception:
        return None


T_JMONTH_START = {'key': 'month', 'transform': _jmonth_start}
T_JMONTH_END = {'key': 'month', 'transform': _jmonth_end}

# ---------- گزینه‌های مشترک فیلترها ----------

STATUS_EMS = [('Pending', 'در انتظار بررسی'), ('inProgress', 'در حال بررسی'),
              ('Done', 'تایید شده'), ('Reject', 'رد شده')]
RISK_EMS = [('norisk', 'بدون خطر'), ('low', 'کم'), ('medium', 'متوسط'), ('high', 'بالا')]
STATUS_REFERR = [('Pending', 'در انتظار'), ('inProgress', 'در جریان'), ('Done', 'انجام شده')]
STATUS_INVITE = [('ارجاع شده', 'ارجاع شده'), ('در حال بررسی', 'در حال بررسی'),
                 ('اتمام بررسی', 'اتمام بررسی')]
GENDERS = [('male', 'مرد'), ('female', 'زن')]
CONFIRM_STATES = [('ok', 'تاییدشده'), ('wait', 'در انتظار'), ('rejected', 'ردشده')]
CONFIRM_STAGE = [('admin', 'مدیر مرکز'), ('tech', 'مسئول فنی'), ('oper', 'نظارت حرفه‌ای'),
                 ('psup', 'ناظر استان'), ('sup', 'ناظر کشور')]
STAGE_COL = {'admin': 'CenterAdminConfirmUserID', 'tech': 'CenterTechConfirmUserID',
             'oper': 'OperatorConfirmUserID', 'psup': 'ProvinceSupervisorConfirmUserID',
             'sup': 'SupervisorConfirmUserID'}
BUDGET_TYPES = [('Main', 'خدمات فردی'), ('Group', 'خدمات گروهی'), ('Job', 'مشاوره شغلی')]
EMS_PAY_STATUS = [('پرداخت شده', 'پرداخت شده'), ('در انتظار پرداخت', 'در انتظار پرداخت'),
                  ('عدم تایید', 'عدم تایید')]

C = None  # برچسب‌ها از catalog در app تزریق می‌شود (اینجا فقط ساختار گزارش)


def _int_filter(key, label, where):
    return {'key': key, 'label': label, 'kind': 'select', 'dict': key,
            'where': where, 'transform': 'int'}


def _date_filters(col):
    return [
        {'key': 'date_from', 'label': 'از تاریخ', 'kind': 'date',
         'where': f'AND {col} >= ?', 'transform': 'jalali_start'},
        {'key': 'date_to', 'label': 'تا تاریخ', 'kind': 'date',
         'where': f'AND {col} <= ?', 'transform': 'jalali_end'},
    ]


PRESETS = [
    # ================================================== جلسات انجام‌شده
    {
        'key': 'done_events',
        'title': 'گزارش جلسات مشاوره انجام‌شده',
        'desc': 'همه جلسات فردی که پایان یافته‌اند — مطابق صفحه «گزارش جلسات مشاوره انجام شده»',
        'icon': '✅', 'category': 'جلسات مشاوره',
        'sql': ("SELECT e.id, u.Name || ' ' || u.Family, e.NID, u.Mobile, "
                "c.CenterTitle, p.Title, ci.Title, a.Name || ' ' || a.Family, "
                "s.Name, e.UserTariff, e.StartDate, e.EndDate "
                "FROM Events e "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Users a ON e.AcceptorID = a.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Services s ON e.ServiceID = s.id "
                "WHERE e.EndDate IS NOT NULL{where}"),
        'order': 'ORDER BY e.StartDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه جلسه', 'type': 'int'},
            {'key': 'client', 'label': 'نام مراجع'},
            {'key': 'nid', 'label': 'کد ملی مراجع'},
            {'key': 'mobile', 'label': 'شماره موبایل'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'service', 'label': 'نوع مشاوره', 'dict': 'service', 'via': 'id', 'raw': 'ServiceID'},
            {'key': 'tariff', 'label': 'تعرفه (ریال)', 'type': 'money'},
            {'key': 'start', 'label': 'تاریخ شروع', 'type': 'date'},
            {'key': 'end', 'label': 'تاریخ پایان', 'type': 'date'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND e.CenterID = ?'),
            {'key': 'adviser', 'label': 'نام مشاور', 'kind': 'text',
             'where': "(a.Name || ' ' || a.Family) LIKE ?", 'transform': 'likeboth'},
            _int_filter('service', 'خدمت', 'AND e.ServiceID = ?'),
            {'key': 'gender', 'label': 'جنسیت', 'kind': 'select', 'options': GENDERS,
             'where': 'AND u.Gender = ?'},
            {'key': 'ems', 'label': 'کیس حاد', 'kind': 'select',
             'options': [('1', 'فقط موارد حاد'), ('0', 'فقط عادی')],
             'where': 'AND e.EMS = ?', 'transform': 'int'},
        ] + _date_filters('e.StartDate'),
    },
    # ================================================== جلسات ناتمام
    {
        'key': 'undone_events',
        'title': 'گزارش جلسات مشاوره ناتمام',
        'desc': 'جلساتی که ثبت شده‌اند اما پایان نیافته‌اند',
        'icon': '⏳', 'category': 'جلسات مشاوره',
        'sql': ("SELECT e.id, u.Name || ' ' || u.Family, e.NID, u.Mobile, "
                "c.CenterTitle, p.Title, ci.Title, a.Name || ' ' || a.Family, "
                "s.Name, e.StartDate, e.RejectedComment "
                "FROM Events e "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Users a ON e.AcceptorID = a.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Services s ON e.ServiceID = s.id "
                "WHERE e.EndDate IS NULL{where}"),
        'order': 'ORDER BY e.StartDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه جلسه', 'type': 'int'},
            {'key': 'client', 'label': 'نام مراجع'},
            {'key': 'nid', 'label': 'کد ملی مراجع'},
            {'key': 'mobile', 'label': 'شماره موبایل'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'service', 'label': 'نوع مشاوره', 'dict': 'service', 'via': 'id', 'raw': 'ServiceID'},
            {'key': 'start', 'label': 'تاریخ شروع', 'type': 'date'},
            {'key': 'reject', 'label': 'دلیل رد/توضیح'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND e.CenterID = ?'),
            {'key': 'adviser', 'label': 'نام مشاور', 'kind': 'text',
             'where': "(a.Name || ' ' || a.Family) LIKE ?", 'transform': 'likeboth'},
            _int_filter('service', 'خدمت', 'AND e.ServiceID = ?'),
        ] + _date_filters('e.StartDate'),
    },
    # ================================================== جلسات گروهی انجام‌شده
    {
        'key': 'group_done',
        'title': 'گزارش جلسات مشاوره گروهی انجام‌شده',
        'desc': 'مطابق صفحه «گزارش جلسات مشاوره گروهی انجام شده» با تعداد حاضران',
        'icon': '👥', 'category': 'جلسات گروهی',
        'sql': ("SELECT ge.id, g.Type, ge.SessionNumber, c.CenterTitle, p.Title, ci.Title, "
                "a.Name || ' ' || a.Family, ge.Topic, ge.StartDate, ge.EndDate, "
                "(SELECT COUNT(*) FROM GroupEventMember gem WHERE gem.GroupEventID = ge.id) "
                "FROM GroupEvents ge "
                "LEFT JOIN Groups g ON ge.GroupID = g.id "
                "LEFT JOIN Centers c ON ge.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Users a ON ge.AcceptorID = a.id "
                "WHERE ge.EndDate IS NOT NULL{where}"),
        'order': 'ORDER BY ge.StartDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه جلسه', 'type': 'int'},
            {'key': 'gtype', 'label': 'نوع گروه', 'dict': {'counseling': 'مشاوره‌ای', 'educational': 'آموزشی'}},
            {'key': 'sess', 'label': 'شماره جلسه', 'type': 'int'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'topic', 'label': 'موضوع'},
            {'key': 'start', 'label': 'تاریخ جلسه', 'type': 'date'},
            {'key': 'end', 'label': 'تاریخ پایان', 'type': 'date'},
            {'key': 'members', 'label': 'تعداد حاضران', 'type': 'int'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND ge.CenterID = ?'),
            {'key': 'adviser', 'label': 'نام مشاور', 'kind': 'text',
             'where': "(a.Name || ' ' || a.Family) LIKE ?", 'transform': 'likeboth'},
            {'key': 'gtype', 'label': 'نوع گروه', 'kind': 'select',
             'options': [('counseling', 'مشاوره‌ای'), ('educational', 'آموزشی')],
             'where': 'AND g.Type = ?'},
        ] + _date_filters('ge.StartDate'),
    },
    # ================================================== جلسات گروهی ناتمام
    {
        'key': 'group_undone',
        'title': 'گزارش جلسات گروهی ناتمام',
        'desc': 'جلسات گروهی ثبت‌شده که هنوز تکمیل نشده‌اند',
        'icon': '🕳️', 'category': 'جلسات گروهی',
        'sql': ("SELECT ge.id, g.Type, ge.SessionNumber, c.CenterTitle, p.Title, ci.Title, "
                "a.Name || ' ' || a.Family, ge.Topic, ge.StartDate "
                "FROM GroupEvents ge "
                "LEFT JOIN Groups g ON ge.GroupID = g.id "
                "LEFT JOIN Centers c ON ge.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Users a ON ge.AcceptorID = a.id "
                "WHERE ge.EndDate IS NULL{where}"),
        'order': 'ORDER BY ge.StartDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه جلسه', 'type': 'int'},
            {'key': 'gtype', 'label': 'نوع گروه', 'dict': {'counseling': 'مشاوره‌ای', 'educational': 'آموزشی'}},
            {'key': 'sess', 'label': 'شماره جلسه', 'type': 'int'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'topic', 'label': 'موضوع'},
            {'key': 'start', 'label': 'تاریخ شروع', 'type': 'date'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND ge.CenterID = ?'),
        ] + _date_filters('ge.StartDate'),
    },
    # ================================================== عملکرد مالی
    {
        'key': 'payments',
        'title': 'عملکرد مالی (به تفکیک مشاور و خدمت)',
        'desc': 'تعداد جلسات و مبالغ هر مشاور در هر خدمت — مطابق صفحه «عملکرد مالی»',
        'icon': '💰', 'category': 'مالی',
        'sql': ("SELECT a.Name || ' ' || a.Family, a.NID, a.Mobile, ed.Name, "
                "e.AcceptorLevel, p.Title, ci.Title, c.CenterTitle, s.Name, "
                "COUNT(*) AS cnt, SUM(e.AcceptorFee) AS fee, SUM(e.SecretaryFee) AS sec, "
                "SUM(e.SupervisorFee) AS sup, SUM(e.CenterFee) AS cfee, SUM(e.UserTariff) AS tariff "
                "FROM Events e "
                "LEFT JOIN Users a ON e.AcceptorID = a.id "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Education ed ON a.EducationID = ed.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Services s ON e.ServiceID = s.id "
                "WHERE 1=1{where} "
                "GROUP BY a.id, s.id"),
        'order': 'ORDER BY cnt DESC',
        'columns': [
            {'key': 'adviser', 'label': 'نام مشاور'},
            {'key': 'nid', 'label': 'کد ملی مشاور'},
            {'key': 'mobile', 'label': 'شماره همراه'},
            {'key': 'edu', 'label': 'مدرک تحصیلی'},
            {'key': 'level', 'label': 'سطح مشاور', 'dict': 'level'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'service', 'label': 'نام سرویس', 'dict': 'service', 'via': 'id', 'raw': 'ServiceID'},
            {'key': 'cnt', 'label': 'تعداد جلسات', 'type': 'int'},
            {'key': 'fee', 'label': 'جمع حق‌الزحمه مشاور (ریال)', 'type': 'money'},
            {'key': 'sec', 'label': 'جمع حق دبیرخانه', 'type': 'money'},
            {'key': 'sup', 'label': 'جمع حق ناظر', 'type': 'money'},
            {'key': 'cfee', 'label': 'جمع سهم مرکز', 'type': 'money'},
            {'key': 'tariff', 'label': 'جمع تعرفه کاربر', 'type': 'money'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND e.CenterID = ?'),
            {'key': 'adviser', 'label': 'نام مشاور', 'kind': 'text',
             'where': "(a.Name || ' ' || a.Family) LIKE ?", 'transform': 'likeboth'},
            _int_filter('service', 'خدمت', 'AND e.ServiceID = ?'),
            {'key': 'confirm', 'label': 'وضعیت تایید', 'kind': 'select',
             'options': [('ok', 'تاییدشده‌ها (۵ مرحله)'), ('no', 'تاییدنشده‌ها')],
             'where': 'AND 1=1'},  # پردازش ویژه در run
            {'key': 'tax_month', 'label': 'ماه مالیات', 'kind': 'text',
             'where': 'AND 1=1'},  # فقط نمایشی — مالیات از جدول ConsultantTax
        ] + _date_filters('e.StartDate'),
        'special': 'payments_confirm',
    },
    # ================================================== به تفکیک خدمت‌گیرنده
    {
        'key': 'recipient',
        'title': 'گزارش به تفکیک خدمت‌گیرنده',
        'desc': 'تعداد و بازه جلسات هر مراجع — مطابق صفحه «گزارش به تفکیک خدمت‌گیرنده»',
        'icon': '🧑‍💼', 'category': 'مالی',
        'sql': ("SELECT u.Name || ' ' || u.Family, u.NID, u.Mobile, p.Title, ci.Title, "
                "c.CenterTitle, s.Name, COUNT(*) AS cnt, "
                "MIN(e.StartDate), MAX(e.StartDate), "
                "SUM(CASE WHEN e.EndDate IS NOT NULL THEN 1 ELSE 0 END) AS done_cnt "
                "FROM Events e "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON c.CityID = ci.id "
                "LEFT JOIN Services s ON e.ServiceID = s.id "
                "WHERE 1=1{where} "
                "GROUP BY u.id, s.id"),
        'order': 'ORDER BY cnt DESC',
        'columns': [
            {'key': 'client', 'label': 'نام خدمت‌گیرنده'},
            {'key': 'nid', 'label': 'کد ملی'},
            {'key': 'mobile', 'label': 'شماره همراه'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'service', 'label': 'خدمت', 'dict': 'service', 'via': 'id', 'raw': 'ServiceID'},
            {'key': 'cnt', 'label': 'تعداد جلسات', 'type': 'int'},
            {'key': 'done', 'label': 'جلسات انجام‌شده', 'type': 'int'},
            {'key': 'first', 'label': 'اولین جلسه', 'type': 'date'},
            {'key': 'last', 'label': 'آخرین جلسه', 'type': 'date'},
        ],
        'filters': [
            {'key': 'month', 'label': 'بر اساس ماه (مثلاً ۱۴۰۴/۰۷)', 'kind': 'text'},
            _int_filter('province', 'استان', 'AND c.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            _int_filter('center', 'مرکز', 'AND e.CenterID = ?'),
            _int_filter('service', 'خدمت', 'AND e.ServiceID = ?'),
            {'key': 'confirm', 'label': 'وضعیت تایید جلسات', 'kind': 'select',
             'options': [('ok', 'تاییدشده‌ها (۵ مرحله)'), ('no', 'تاییدنشده‌ها')],
             'where': 'AND 1=1'},
        ],
        'special': 'recipient_month',
    },
    # ================================================== ارجاعات سها
    {
        'key': 'referrs',
        'title': 'ارجاع‌های سها',
        'desc': 'ارجاع‌های دریافتی از سامانه سها — مطابق صفحه «ارجاعات سها»',
        'icon': '🔗', 'category': 'کاربران و درخواست‌ها',
        'sql': ("SELECT r.id, r.RefID, u.NID, u.Name || ' ' || u.Family, u.Mobile, "
                "p.Title, ci.Title, r.Type, r.ServiceID, r.Description, "
                "(SELECT COUNT(*) FROM Events ev WHERE ev.RefID = r.RefID) AS ev_cnt, "
                "r.Status, r.CreationDate, c.CenterTitle, ac.Name || ' ' || ac.Family "
                "FROM Referrs r "
                "LEFT JOIN Users u ON r.UserID = u.id "
                "LEFT JOIN Provinces p ON r.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON r.CityID = ci.id "
                "LEFT JOIN Centers c ON r.CenterID = c.id "
                "LEFT JOIN Users ac ON r.AcceptorID = ac.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY r.CreationDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه', 'type': 'int'},
            {'key': 'refid', 'label': 'کد ارجاع سها'},
            {'key': 'nid', 'label': 'کد ملی'},
            {'key': 'user', 'label': 'نام کاربر'},
            {'key': 'mobile', 'label': 'موبایل'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهر'},
            {'key': 'type', 'label': 'نوع ارجاع', 'dict': {'soha': 'سها', 'inPerson': 'حضوری'}},
            {'key': 'service', 'label': 'نوع خدمت', 'dict': 'service', 'via': 'soha', 'raw': 'ServiceID'},
            {'key': 'desc', 'label': 'توضیحات'},
            {'key': 'events', 'label': 'تعداد جلسه', 'type': 'int'},
            {'key': 'status', 'label': 'وضعیت', 'dict': {'Pending': 'در انتظار', 'inProgress': 'در جریان', 'Done': 'انجام شده'}},
            {'key': 'date', 'label': 'تاریخ', 'type': 'date'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'acceptor', 'label': 'مشاور پذیرنده'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND r.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND r.CityID = ?', 'transform': 'int', 'depends': 'province'},
            {'key': 'status', 'label': 'وضعیت', 'kind': 'select', 'options': STATUS_REFERR,
             'where': 'AND r.Status = ?'},
            {'key': 'rtype', 'label': 'نوع ارجاع', 'kind': 'select',
             'options': [('soha', 'سها'), ('inPerson', 'حضوری')], 'where': 'AND r.Type = ?'},
            {'key': 'service', 'label': 'نوع خدمت', 'kind': 'select', 'dict': 'services_soha',
             'where': 'AND r.ServiceID = ?', 'transform': 'int'},
        ] + _date_filters('r.CreationDate'),
    },
    # ================================================== درخواست‌های رزرو
    {
        'key': 'reserve_requests',
        'title': 'درخواست‌های رزرو کاربران',
        'desc': 'مطابق صفحه «درخواست‌های رزرو کاربران»',
        'icon': '📅', 'category': 'کاربران و درخواست‌ها',
        'sql': ("SELECT rr.id, u.NID, u.Name || ' ' || u.Family, u.Mobile, "
                "p.Title, ci.Title, rr.Status, rr.Description, rr.CreationDate, "
                "c.CenterTitle, ar.Name || ' ' || ar.Family "
                "FROM ReferrsRequest rr "
                "LEFT JOIN Users u ON rr.UserID = u.id "
                "LEFT JOIN Provinces p ON rr.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON rr.CityID = ci.id "
                "LEFT JOIN Centers c ON rr.CenterID = c.id "
                "LEFT JOIN Users ar ON rr.AdminReferrerID = ar.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY rr.CreationDate DESC',
        'columns': [
            {'key': 'id', 'label': 'کد ارجاع', 'type': 'int'},
            {'key': 'nid', 'label': 'کد ملی'},
            {'key': 'user', 'label': 'نام کاربر'},
            {'key': 'mobile', 'label': 'موبایل'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهر'},
            {'key': 'status', 'label': 'وضعیت', 'dict': {'Pending': 'در انتظار', 'inProgress': 'در جریان', 'Done': 'انجام شده'}},
            {'key': 'desc', 'label': 'توضیحات'},
            {'key': 'date', 'label': 'تاریخ', 'type': 'date'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'admin', 'label': 'معرف اداری'},
        ],
        'filters': [
            _int_filter('province', 'استان', 'AND rr.ProvinceID = ?'),
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND rr.CityID = ?', 'transform': 'int', 'depends': 'province'},
            {'key': 'status', 'label': 'وضعیت', 'kind': 'select', 'options': STATUS_REFERR,
             'where': 'AND rr.Status = ?'},
        ] + _date_filters('rr.CreationDate'),
    },
    # ================================================== موارد حاد
    {
        'key': 'ems',
        'title': 'موارد حاد',
        'desc': 'مطابق صفحه «موارد حاد» — شدت خطر، وضعیت بررسی و پرداخت',
        'icon': '🚨', 'category': 'موارد حاد',
        'sql': ("SELECT ee.id, e.NID, u.Name || ' ' || u.Family, "
                "c.ProvinceTitle, c.CityTitle, a.Name || ' ' || a.Family, a.Mobile, "
                "ee.EMSType, ee.SuicidalFrom, ee.SuicidalRiskLevel, ee.Status, "
                "ee.FinancialAssistanceRequest, ee.HadPaymentAmount, ee.HadPaymentStatus, "
                "ee.HadPaymentDescription, ee.DateTime, "
                "(SELECT GROUP_CONCAT(Comment, ' | ') FROM EventEmsComments WHERE EventEmsID = ee.id) AS notes "
                "FROM EventsEms ee "
                "LEFT JOIN Events e ON ee.EventID = e.id "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Users a ON e.AcceptorID = a.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY ee.DateTime DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه', 'type': 'int'},
            {'key': 'nid', 'label': 'کدملی'},
            {'key': 'user', 'label': 'نام و نام خانوادگی'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'adviser', 'label': 'نام مشاور'},
            {'key': 'amobile', 'label': 'موبایل مشاور'},
            {'key': 'emstype', 'label': 'نوع مورد حاد'},
            {'key': 'suicidal', 'label': 'عوامل خودکشی'},
            {'key': 'risk', 'label': 'شدت خطر', 'dict': {'low': 'کم', 'medium': 'متوسط', 'high': 'بالا', 'norisk': 'بدون خطر'}},
            {'key': 'status', 'label': 'وضعیت', 'dict': {'Pending': 'در انتظار بررسی', 'inProgress': 'در حال بررسی', 'Done': 'تایید شده', 'Reject': 'رد شده'}},
            {'key': 'finreq', 'label': 'درخواست کمک مالی', 'dict': 'yn01'},
            {'key': 'amount', 'label': 'مبلغ درخواستی (ریال)', 'type': 'money'},
            {'key': 'paystatus', 'label': 'وضعیت پرداخت'},
            {'key': 'paydesc', 'label': 'دلیل پرداخت'},
            {'key': 'date', 'label': 'تاریخ', 'type': 'date'},
            {'key': 'notes', 'label': 'نظرات کمیسیون'},
        ],
        'filters': [
            {'key': 'province', 'label': 'استان', 'kind': 'select', 'dict': 'provinces',
             'where': 'AND c.ProvinceID = ?', 'transform': 'int'},
            {'key': 'risk', 'label': 'شدت خطر', 'kind': 'select', 'options': RISK_EMS,
             'where': 'AND ee.SuicidalRiskLevel = ?'},
            {'key': 'status', 'label': 'وضعیت', 'kind': 'select', 'options': STATUS_EMS,
             'where': 'AND ee.Status = ?'},
            {'key': 'pay', 'label': 'وضعیت پرداخت', 'kind': 'select', 'options': EMS_PAY_STATUS,
             'where': 'AND ee.HadPaymentStatus = ?'},
            {'key': 'nid', 'label': 'کد ملی', 'kind': 'text', 'where': 'AND e.NID LIKE ?',
             'transform': 'likeboth'},
        ] + _date_filters('ee.DateTime'),
    },
    # ================================================== بررسی مشاوره‌ها (تایید ۵ مرحله)
    {
        'key': 'confirmations',
        'title': 'بررسی مشاوره‌ها (تایید چندمرحله‌ای)',
        'desc': 'وضعیت تایید ۵ مرحله‌ای هر جلسه — مطابق صفحه «بررسی مشاوره‌ها»',
        'icon': '🕵️', 'category': 'جلسات مشاوره',
        'sql': ("SELECT e.id, e.RefID, e.NID, u.Name || ' ' || u.Family, u.Mobile, "
                "s.Name, e.ContractID, e.EMS, a.Name || ' ' || a.Family, "
                "c.ProvinceTitle, c.CityTitle, c.CenterTitle, e.StartDate, "
                "CASE WHEN e.CenterAdminConfirmUserID IS NOT NULL THEN '✔ تایید' ELSE '⏳ در انتظار' END, "
                "CASE WHEN e.CenterTechConfirmUserID IS NOT NULL THEN '✔ تایید' ELSE '⏳ در انتظار' END, "
                "CASE WHEN e.OperatorConfirmUserID IS NOT NULL THEN '✔ تایید' ELSE '⏳ در انتظار' END, "
                "CASE WHEN e.ProvinceSupervisorConfirmUserID IS NOT NULL THEN '✔ تایید' ELSE '⏳ در انتظار' END, "
                "CASE WHEN e.SupervisorConfirmUserID IS NOT NULL THEN '✔ تایید' ELSE '⏳ در انتظار' END, "
                "CASE WHEN e.RejectedByUserID IS NOT NULL THEN '🚫 رد شده' ELSE '' END "
                "FROM Events e "
                "LEFT JOIN Users u ON e.UserID = u.id "
                "LEFT JOIN Users a ON e.AcceptorID = a.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Services s ON e.ServiceID = s.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY e.StartDate DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه', 'type': 'int'},
            {'key': 'refid', 'label': 'شناسه ارجاع'},
            {'key': 'nid', 'label': 'کدملی'},
            {'key': 'user', 'label': 'نام کاربر'},
            {'key': 'mobile', 'label': 'شماره موبایل'},
            {'key': 'service', 'label': 'خدمت', 'dict': 'service', 'via': 'id', 'raw': 'ServiceID'},
            {'key': 'contract', 'label': 'قرارداد', 'type': 'int'},
            {'key': 'ems', 'label': 'کیس حاد', 'dict': 'bit'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'date', 'label': 'تاریخ', 'type': 'date'},
            {'key': 'st_admin', 'label': 'مدیر مرکز'},
            {'key': 'st_tech', 'label': 'مسئول فنی'},
            {'key': 'st_oper', 'label': 'نظارت حرفه‌ای'},
            {'key': 'st_psup', 'label': 'ناظر استان'},
            {'key': 'st_sup', 'label': 'ناظر کشور'},
            {'key': 'rejected', 'label': 'وضعیت رد'},
        ],
        'filters': [
            {'key': 'province', 'label': 'استان', 'kind': 'select', 'dict': 'provinces',
             'where': 'AND c.ProvinceID = ?', 'transform': 'int'},
            {'key': 'city', 'label': 'شهرستان', 'kind': 'select', 'dict': 'cities',
             'where': 'AND c.CityID = ?', 'transform': 'int', 'depends': 'province'},
            {'key': 'center', 'label': 'مرکز', 'kind': 'select', 'dict': 'centers',
             'where': 'AND e.CenterID = ?', 'transform': 'int'},
            {'key': 'adviser', 'label': 'نام مشاور', 'kind': 'text',
             'where': "(a.Name || ' ' || a.Family) LIKE ?", 'transform': 'likeboth'},
            {'key': 'service', 'label': 'خدمت', 'kind': 'select', 'dict': 'services',
             'where': 'AND e.ServiceID = ?', 'transform': 'int'},
            {'key': 'stage', 'label': 'مرحله تایید', 'kind': 'select', 'options': CONFIRM_STAGE,
             'where': 'AND 1=1'},
            {'key': 'cstate', 'label': 'وضعیت تایید', 'kind': 'select', 'options': CONFIRM_STATES,
             'where': 'AND 1=1'},
            {'key': 'ems', 'label': 'کیس حاد', 'kind': 'select',
             'options': [('1', '⭕ فقط کیس حاد'), ('0', '😇 عادی')],
             'where': 'AND e.EMS = ?', 'transform': 'int'},
        ] + _date_filters('e.StartDate'),
        'special': 'confirm_stage',
    },
    # ================================================== کاربران معرفی‌شده
    {
        'key': 'invitepersons',
        'title': 'کاربران معرفی‌شده',
        'desc': 'مطابق صفحه «کاربران معرفی شده» با آپلود اکسل در برنامه اصلی',
        'icon': '🤝', 'category': 'کاربران و درخواست‌ها',
        'sql': ("SELECT ip.ID, ip.GroupName, ip.GroupID, ip.Name, ip.Mobile, ip.Phone, "
                "ip.NID, ip.Status, ip.Response, p.Title, ci.Title, c.CenterTitle, "
                "ip.CreateTime, ip.UpdateTime, ip.Description "
                "FROM InvitePersons ip "
                "LEFT JOIN Provinces p ON ip.ProvinceID = p.id "
                "LEFT JOIN Cities ci ON ip.CityID = ci.id "
                "LEFT JOIN Centers c ON ip.CenterID = c.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY ip.CreateTime DESC',
        'columns': [
            {'key': 'id', 'label': 'ردیف', 'type': 'int'},
            {'key': 'group', 'label': 'نام گروه'},
            {'key': 'gid', 'label': 'شناسه گروه'},
            {'key': 'name', 'label': 'نام'},
            {'key': 'mobile', 'label': 'شماره اول'},
            {'key': 'phone', 'label': 'شماره دوم'},
            {'key': 'nid', 'label': 'کدملی'},
            {'key': 'status', 'label': 'وضعیت'},
            {'key': 'result', 'label': 'نتیجه'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'city', 'label': 'شهرستان'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'created', 'label': 'تاریخ ثبت', 'type': 'date'},
            {'key': 'updated', 'label': 'آخرین تغییرات', 'type': 'date'},
            {'key': 'desc', 'label': 'اطلاعات تکمیلی'},
        ],
        'filters': [
            {'key': 'province', 'label': 'استان', 'kind': 'select', 'dict': 'provinces',
             'where': 'AND ip.ProvinceID = ?', 'transform': 'int'},
            {'key': 'status', 'label': 'وضعیت', 'kind': 'select', 'options': STATUS_INVITE,
             'where': 'AND ip.Status = ?'},
            {'key': 'q', 'label': 'جستجو (نام/کدملی)', 'kind': 'text',
             'where': '(ip.Name LIKE ? OR CAST(ip.NID AS TEXT) LIKE ?)', 'transform': 'like2'},
        ] + _date_filters('ip.CreateTime'),
    },
    # ================================================== فعالیت کاربران
    {
        'key': 'logs',
        'title': 'گزارش فعالیت کاربران',
        'desc': 'لاگ رخدادهای سامانه — مطابق صفحه «گزارش فعالیت کاربران»',
        'icon': '📜', 'category': 'مدیریت',
        'sql': ("SELECT l.id, l.uid, u.Name || ' ' || u.Family, l.Category, "
                "l.Description, l.Level, l.IP, l.Timestamp "
                "FROM Log l LEFT JOIN Users u ON l.uid = u.id WHERE 1=1{where}"),
        'order': 'ORDER BY l.Timestamp DESC',
        'columns': [
            {'key': 'id', 'label': 'کد', 'type': 'int'},
            {'key': 'uid', 'label': 'کد کاربر', 'type': 'int'},
            {'key': 'user', 'label': 'نام کاربر'},
            {'key': 'cat', 'label': 'دسته'},
            {'key': 'desc', 'label': 'توضیح'},
            {'key': 'level', 'label': 'سطح', 'dict': {0: 'اطلاع', 1: 'هشدار', 2: 'خطا', 3: 'بحرانی', 4: 'امنیتی', 5: 'ورود', 6: 'سیستم'}},
            {'key': 'ip', 'label': 'IP'},
            {'key': 'date', 'label': 'تاریخ', 'type': 'date'},
        ],
        'filters': [
            {'key': 'q', 'label': 'جستجو در توضیح', 'kind': 'text',
             'where': 'l.Description LIKE ?', 'transform': 'likeboth'},
            {'key': 'cat', 'label': 'دسته', 'kind': 'text', 'where': 'l.Category = ?'},
            {'key': 'uid', 'label': 'کد کاربر', 'kind': 'text', 'where': 'l.uid = ?',
             'transform': 'int'},
        ] + _date_filters('l.Timestamp'),
    },
    # ================================================== کاربران
    {
        'key': 'users',
        'title': 'مدیریت کاربران',
        'desc': 'همه کاربران سامانه — مطابق صفحه «مدیریت کاربران» (رمزها هرگز نمایش داده نمی‌شوند)',
        'icon': '👤', 'category': 'کاربران و درخواست‌ها',
        'sql': ("SELECT u.id, u.Username, u.Name, u.Family, u.Father, u.Gender, "
                "u.Mobile, p.Title, ed.Name, u.Birthday, u.SignupDate, u.LastLogin, "
                "ur.Title AS role_title, u.Blocked "
                "FROM Users u "
                "LEFT JOIN Provinces p ON u.ProvinceID = p.id "
                "LEFT JOIN Education ed ON u.EducationID = ed.id "
                "LEFT JOIN UserRoles ur0 ON ur0.UserID = u.id AND ur0.RoleID = ( "
                "   SELECT ur.RoleID FROM UserRoles ur WHERE ur.UserID = u.id LIMIT 1) "
                "LEFT JOIN Roles ur ON ur.id = ur0.RoleID "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY u.SignupDate DESC',
        'columns': [
            {'key': 'id', 'label': 'کد', 'type': 'int'},
            {'key': 'username', 'label': 'نام‌کاربری'},
            {'key': 'name', 'label': 'نام'},
            {'key': 'family', 'label': 'نام خانوادگی'},
            {'key': 'father', 'label': 'نام‌پدر'},
            {'key': 'gender', 'label': 'جنسیت', 'dict': {'male': 'مرد', 'female': 'زن'}},
            {'key': 'mobile', 'label': 'شماره‌همراه'},
            {'key': 'province', 'label': 'استان'},
            {'key': 'edu', 'label': 'تحصیلات'},
            {'key': 'bday', 'label': 'تاریخ تولد', 'type': 'date', 'time': False},
            {'key': 'signup', 'label': 'تاریخ ثبت‌نام', 'type': 'date'},
            {'key': 'login', 'label': 'آخرین ورود', 'type': 'date'},
            {'key': 'role', 'label': 'نقش'},
            {'key': 'blocked', 'label': 'مسدود', 'dict': 'yn01'},
        ],
        'filters': [
            {'key': 'province', 'label': 'استان', 'kind': 'select', 'dict': 'provinces',
             'where': 'AND u.ProvinceID = ?', 'transform': 'int'},
            {'key': 'gender', 'label': 'جنسیت', 'kind': 'select', 'options': GENDERS,
             'where': 'AND u.Gender = ?'},
            {'key': 'q', 'label': 'جستجو (نام/کدملی/موبایل)', 'kind': 'text',
             'where': "(u.Name || ' ' || u.Family LIKE ? OR CAST(u.NID AS TEXT) LIKE ? "
                      "OR CAST(u.Mobile AS TEXT) LIKE ? OR u.Username LIKE ?)",
             'transform': 'like4'},
        ] + _date_filters('u.SignupDate'),
    },
    # ================================================== مالیات مشاوران
    {
        'key': 'consultant_tax',
        'title': 'مالیات مشاوران',
        'desc': 'رکوردهای مالیات محاسبه‌شده — مطابق صفحه «مدیریت مالیات مشاوران»',
        'icon': '🧾', 'category': 'مالی',
        'sql': ("SELECT t.id, t.NID, u.Name, u.Family, t.TaxAmount, t.ExemptionMonths, "
                "t.MultiEmployerMonth, t.MultiEmployerYear, t.TotalPayment, t.Year, t.Month "
                "FROM ConsultantTax t LEFT JOIN Users u ON t.NID = u.NID "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY t.Year DESC, t.Month DESC',
        'columns': [
            {'key': 'id', 'label': 'ردیف', 'type': 'int'},
            {'key': 'nid', 'label': 'کد ملی'},
            {'key': 'name', 'label': 'نام'},
            {'key': 'family', 'label': 'نام خانوادگی'},
            {'key': 'tax', 'label': 'مالیات (ریال)', 'type': 'money'},
            {'key': 'exempt', 'label': 'ماه معافیت', 'type': 'int'},
            {'key': 'memp_m', 'label': 'چند کارفرما (ماه)', 'type': 'int'},
            {'key': 'memp_y', 'label': 'چند کارفرما (سال)', 'type': 'int'},
            {'key': 'total', 'label': 'حق‌الزحمه (ریال)', 'type': 'money'},
            {'key': 'year', 'label': 'سال', 'type': 'int'},
            {'key': 'month', 'label': 'ماه', 'type': 'int'},
        ],
        'filters': [
            {'key': 'nid', 'label': 'کد ملی', 'kind': 'text',
             'where': 'CAST(t.NID AS TEXT) LIKE ?', 'transform': 'likeboth'},
            {'key': 'year', 'label': 'سال', 'kind': 'text', 'where': 't.Year = ?', 'transform': 'int'},
            {'key': 'month', 'label': 'ماه', 'kind': 'text', 'where': 't.Month = ?', 'transform': 'int'},
        ],
    },
    # ================================================== سهمیه‌ها
    {
        'key': 'budgets',
        'title': 'سهمیه‌های خدمات (بودجه)',
        'desc': 'وضعیت سهمیه‌های کشوری و مصرف آن‌ها — مطابق صفحه «مدیریت سهمیه کشور»',
        'icon': '🎯', 'category': 'مدیریت',
        'sql': ("SELECT b.Id, b.Title, b.Type, b.Amount, b.Used, b.Reserved, b.Remained, "
                "b.Assigned, ROUND(CASE WHEN b.Amount > 0 THEN b.Used * 100.0 / b.Amount "
                "ELSE 0 END, 1) AS pct, b.StartDate, b.EndDate, b.AmountBefore "
                "FROM Budget b WHERE 1=1{where}"),
        'order': 'ORDER BY b.Id DESC',
        'columns': [
            {'key': 'id', 'label': '#', 'type': 'int'},
            {'key': 'title', 'label': 'عنوان سهمیه'},
            {'key': 'type', 'label': 'نوع', 'dict': {'Main': 'خدمات فردی', 'Group': 'خدمات گروهی', 'Job': 'مشاوره شغلی'}},
            {'key': 'amount', 'label': 'سهمیه تخصیصی', 'type': 'decimal'},
            {'key': 'used', 'label': 'استفاده شده', 'type': 'decimal'},
            {'key': 'reserved', 'label': 'رزرو', 'type': 'decimal'},
            {'key': 'remained', 'label': 'مانده', 'type': 'decimal'},
            {'key': 'assigned', 'label': 'تخصیص نیافته', 'type': 'decimal'},
            {'key': 'pct', 'label': 'درصد مصرف', 'type': 'decimal'},
            {'key': 'start', 'label': 'تاریخ شروع', 'type': 'date', 'time': False},
            {'key': 'end', 'label': 'تاریخ پایان', 'type': 'date', 'time': False},
        ],
        'filters': [
            {'key': 'btype', 'label': 'نوع سهمیه', 'kind': 'select', 'options': BUDGET_TYPES,
             'where': 'AND b.Type = ?'},
        ],
    },
    # ================================================== رزروهای جلسات
    {
        'key': 'reserves',
        'title': 'رزرو جلسات مشاوره',
        'desc': 'همه رزروهای ثبت‌شده وقت مشاوره',
        'icon': '🗓️', 'category': 'کاربران و درخواست‌ها',
        'sql': ("SELECT er.id, er.EventID, u.Name || ' ' || u.Family, u.NID, "
                "a.Name || ' ' || a.Family, er.Date, c.CenterTitle, p.Title "
                "FROM EventReserves er "
                "LEFT JOIN Users u ON er.UserID = u.id "
                "LEFT JOIN Users a ON er.AcceptorID = a.id "
                "LEFT JOIN Events e ON er.EventID = e.id "
                "LEFT JOIN Centers c ON e.CenterID = c.id "
                "LEFT JOIN Provinces p ON c.ProvinceID = p.id "
                "WHERE 1=1{where}"),
        'order': 'ORDER BY er.Date DESC',
        'columns': [
            {'key': 'id', 'label': 'شناسه', 'type': 'int'},
            {'key': 'event', 'label': 'شناسه جلسه', 'type': 'int'},
            {'key': 'user', 'label': 'مراجع'},
            {'key': 'nid', 'label': 'کد ملی'},
            {'key': 'adviser', 'label': 'مشاور'},
            {'key': 'date', 'label': 'تاریخ رزرو', 'type': 'date'},
            {'key': 'center', 'label': 'مرکز'},
            {'key': 'province', 'label': 'استان'},
        ],
        'filters': [
            {'key': 'province', 'label': 'استان', 'kind': 'select', 'dict': 'provinces',
             'where': 'AND c.ProvinceID = ?', 'transform': 'int'},
            {'key': 'q', 'label': 'جستجو (نام/کدملی)', 'kind': 'text',
             'where': "(u.Name || ' ' || u.Family LIKE ? OR CAST(u.NID AS TEXT) LIKE ?)",
             'transform': 'like2'},
        ] + _date_filters('er.Date'),
    },
]

PRESET_BY_KEY = {p['key']: p for p in PRESETS}


# ---------- فیلترهای ویژه (پردازش در app) ----------

def confirm_stage_where(stage, state):
    """فیلتر مرحله/وضعیت تایید برای گزارش confirmations و payments"""
    col = STAGE_COL.get(stage)
    if not col:
        return None, None
    if state == 'ok':
        return f'AND e.{col} IS NOT NULL', None
    if state == 'wait':
        return f'AND e.{col} IS NULL', None
    if state == 'rejected':
        return 'AND e.RejectedByUserID IS NOT NULL', None
    return None, None


def all_confirmed_where(state):
    """تایید ۵ مرحله‌ای برای payments/recipient"""
    if state == 'ok':
        return (' AND e.CenterAdminConfirmUserID IS NOT NULL '
                'AND e.CenterTechConfirmUserID IS NOT NULL '
                'AND e.OperatorConfirmUserID IS NOT NULL '
                'AND e.ProvinceSupervisorConfirmUserID IS NOT NULL '
                'AND e.SupervisorConfirmUserID IS NOT NULL')
    if state == 'no':
        return (' AND (e.CenterAdminConfirmUserID IS NULL '
                'OR e.CenterTechConfirmUserID IS NULL '
                'OR e.OperatorConfirmUserID IS NULL '
                'OR e.ProvinceSupervisorConfirmUserID IS NULL '
                'OR e.SupervisorConfirmUserID IS NULL)')
    return None

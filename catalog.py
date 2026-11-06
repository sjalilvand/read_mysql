# -*- coding: utf-8 -*-
"""کاتالوگ دانش دیتابیس «راه زندگی» — برچسب‌های فارسی، ارتباط‌ها و دیکشنری مقادیر.

این فایل قلب «دقت» برنامه است:
  - TABLES: نام فارسی و توضیح همه ۷۵ جدول
  - COLS:  برچسب فارسی ستون‌های جدول‌های اصلی
  - FK:    هر ستونِ کلید خارجی به جدول والد و ستون نمایش می‌رسد (اتو-جوی)
  - ENUMS: دیکشنری مقادیر وضعیت/نوع (استاتیک) + دینامیک (Services/Roles/... از خود دیتابیس)
  - DATES: ستون‌های تاریخ هر جدول برای فیلتر و نمایش شمسی
  - SENSITIVE: ستون‌های محرمانه (هش رمز، کلید نشست...) که هرگز نمایش داده نمی‌شوند
"""

# ----------------------------------------------------------------------
# نام فارسی جدول‌ها
# ----------------------------------------------------------------------
TABLES = {
    'ApiReports': ('گزارش‌های API', 'درخواست‌های گزارش‌گیری از سرویس سها و وضعیت آن‌ها'),
    'ApiStates': ('وضعیت API — شهرها', 'کد شهرها برای فراخوانی API سها'),
    'ApiTokens': ('توکن‌های API', 'توکن‌های احراز هویت سرویس‌های خارجی'),
    'Budget': ('سهمیه‌های خدمات (بودجه)', 'سهمیه‌های کشوری خدمات فردی/گروهی/شغلی'),
    'BudgetCenter': ('تخصیص سهمیه به مرکز', 'سهم تخصیصی هر مرکز از سهمیه‌ها'),
    'BudgetCity': ('تخصیص سهمیه به شهرستان', 'سهم تخصیصی هر شهرستان از سهمیه‌ها'),
    'BudgetProvince': ('تخصیص سهمیه به استان', 'سهم تخصیصی هر استان از سهمیه‌ها'),
    'CareerCounseling': ('مشاوره شغلی (اداره کار)', 'درخواست‌های مشاوره شغلی از سامانه بهزیستی/اداره کار'),
    'CenterBankAccount': ('حساب‌های بانکی مراکز', 'اطلاعات حساب بانکی مراکز برای تسویه'),
    'CenterCategories': ('دسته‌بندی مراکز', 'انواع استقرار مرکز (مستقر در اداره، مستقل و...)'),
    'CenterEquipments': ('تجهیزات مراکز', 'تجهیزات ثبت‌شده هر مرکز'),
    'Centers': ('مراکز و کلینیک‌ها', 'فهرست مراکز خدمات مشاوره سراسر کشور'),
    'Cities': ('شهرستان‌ها', 'شهرستان‌های کشور با کد API سها'),
    'ConsultScope': ('حوزه‌های مشاوره', 'حوزه‌های تخصصی مشاوره'),
    'ConsultantCourses': ('دوره‌های آموزشی مشاوران', 'دوره‌های گذرانده‌شده مشاوران'),
    'ConsultantEducation': ('تحصیلات مشاوران', 'مدارک تحصیلی مشاوران'),
    'ConsultantExperience': ('سوابق کاری مشاوران', 'تجربه‌های کاری مشاوران'),
    'ConsultantHistory': ('تاریخچه اشتغال مشاوران', 'تاریخچه همکاری مشاوران'),
    'ConsultantTax': ('مالیات مشاوران', 'مالیات محاسبه‌شده ماهانه مشاوران'),
    'ConsultantTeachingExperience': ('سوابق تدریس مشاوران', 'تجربه‌های تدریس مشاوران'),
    'CorporateContractCoupons': ('کدهای تخفیف قرارداد', 'کوپن‌های شناسایی مشمولان قرارداد'),
    'CorporateContractNIDs': ('کدهای ملی قرارداد', 'مشمولان قرارداد سازمانی بر اساس کد ملی'),
    'CorporateContractServices': ('خدمات و تعرفه قراردادها', 'تعرفه هر سطح مشاور برای هر خدمت در قرارداد'),
    'CorporateContracts': ('قراردادهای سازمانی', 'قراردادهای تشخیص خودکار مشمولان'),
    'CorporateCustomers': ('مشتریان سازمانی', 'سازمان‌های طرف قرارداد'),
    'Disorders': ('اختلالات', 'طبقه‌بندی درختی اختلالات روانی'),
    'Education': ('مدارک تحصیلی', 'سطح تحصیلات'),
    'EquipmentItems': ('اقلام تجهیزات', 'اقلام استاندارد تجهیزات مراکز'),
    'EventChildPsychology': ('ارزیابی روانشناسی کودک', 'فرم مشاهده بالینی کودک (ضمن جلسه)'),
    'EventComments': ('یادداشت‌های جلسه', 'یادداشت مشاور روی هر جلسه'),
    'EventDisorders': ('اختلالات جلسه', 'اختلالات ثبت‌شده برای هر جلسه'),
    'EventEmsComments': ('نظرات موارد حاد', 'گزارش کمیسیون و نظرات روی مورد حاد'),
    'EventHeadMap': ('نقشه مغزی', 'نتایج نقشه‌برداری مغز (QEEG)'),
    'EventMedicine': ('داروهای تجویزی', 'داروهای تجویزشده در جلسه روانپزشکی'),
    'EventNeuroFeedback': ('جلسات نوروفیدبک', 'پروتکل و نتایج قبل/بعد نوروفیدبک'),
    'EventPersonal': ('موضوع جلسه', 'موضوع (ازدواج، تحصیلی و...) و شرح جلسه'),
    'EventPsychology': ('شرح حال بالینی جلسه', 'معاینه وضعیت روانی (MSE) و شرح حال کامل'),
    'EventQuizzes': ('آزمون‌های جلسه', 'آزمون‌های تجویزشده در جلسه'),
    'EventReferrs': ('ارجاع جلسه به مشاور دیگر', 'ارجاع داخلی جلسات بین مشاوران'),
    'EventReserves': ('رزرو جلسات', 'رزروهای ثبت‌شده وقت مشاوره'),
    'Events': ('جلسات مشاوره', 'جدول اصلی — همه جلسات فردی و خدمات'),
    'EventsEms': ('موارد حاد', 'موارد حاد (آسیب به خود) و فرآیند بررسی و پرداخت'),
    'Expenses': ('هزینه‌ها', 'هزینه‌های ثبت‌شده مراکز'),
    'Files': ('فایل‌ها', 'فایل‌های بارگذاری‌شده (رزومه، نقشه مغزی و...)'),
    'GroupEventMember': ('حضور در جلسات گروهی', 'افراد حاضر در هر جلسه گروهی'),
    'GroupEventReserves': ('رزرو جلسات گروهی', 'رزروهای جلسات گروهی'),
    'GroupEvents': ('جلسات گروهی', 'جلسات برگزارشده گروه‌ها'),
    'GroupMembers': ('اعضای گروه‌ها', 'اعضای ثبت‌شده هر گروه'),
    'Groups': ('گروه‌ها', 'گروه‌های مشاوره‌ای و آموزشی'),
    'Helps': ('راهنماهای سامانه', 'فایل‌های راهنمای هر نقش'),
    'Incomes': ('درآمدها', 'درآمدهای ثبت‌شده مراکز'),
    'InvitePersons': ('کاربران معرفی‌شده', 'افراد معرفی‌شده از سوی گروه‌ها/سازمان‌ها'),
    'JobsList': ('فهرست مشاغل', 'عناوین شغلی نظام صنفی'),
    'Log': ('لاگ فعالیت کاربران', 'رخدادهای سامانه (ورود، پذیرش، API و...)'),
    'Marriage': ('وضعیت تاهل', 'انواع وضعیت تاهل'),
    'Messages': ('پیام‌های داخلی', 'پیام‌های بین کاربران سامانه'),
    'Notifications': ('اعلان‌ها', 'اعلان‌های سیستمی'),
    'NotificationsQueue': ('صف اعلان‌ها', 'اعلان‌های در صف ارسال'),
    'Provinces': ('استان‌ها', 'استان‌های کشور با کد API'),
    'ReferrFollowUps': ('پیگیری ارجاع‌ها', 'یادداشت‌های پیگیری ارجاع سها'),
    'Referrs': ('ارجاع‌های سها', 'ارجاع دریافتی از سامانه سها'),
    'ReferrsRequest': ('درخواست‌های رزرو کاربران', 'درخواست رزروی که کاربران ثبت کرده‌اند'),
    'Religion': ('ادیان', 'فهرست ادیان'),
    'Roles': ('نقش‌ها', 'نقش‌های سامانه'),
    'SMS': ('پیامک‌ها', 'همه پیامک‌های ارسالی سامانه'),
    'Services': ('خدمات', 'انواع خدمت (مشاوره فردی، گروهی، نوروفیدبک و...)'),
    'Sessions': ('نشست‌های ورود', 'نشست‌های فعال کاربران'),
    'Settings': ('تنظیمات سیستم', 'کلید/مقدار تنظیمات'),
    'SpecialOccasions': ('مناسبت‌ها', 'بنر مناسبت‌های نمایشی'),
    'UserMFA': ('رمز دوم کاربران', 'تنظیمات ورود دومرحله‌ای'),
    'UserPasskeys': ('کلیدهای عبور', 'Passkeyهای ثبت‌شده کاربران'),
    'UserRoles': ('نقش‌ها و قراردادهای کاربران', 'دسترسی‌ها و قرارداد هر کاربر'),
    'UserTicket': ('تیکت‌های پشتیبانی', 'تیکت‌های ثبت‌شده کاربران'),
    'Users': ('کاربران', 'همه کاربران (مراجع، مشاوران، مدیران و...)'),
    '_fix_endrefer': ('جدول فنی اصلاح ارجاع', 'جدول کمکی فنی'),
}

# ----------------------------------------------------------------------
# برچسب ستون‌ها (جدول‌های اصلی) — بقیه جدول‌ها نام اصلی ستون نمایش داده می‌شود
# ----------------------------------------------------------------------
COLS = {
    'Events': {
        'id': 'شناسه', 'UserID': 'مراجع', 'NID': 'کد ملی مراجع',
        'TrackingCode': 'کد رهگیری', 'CenterID': 'مرکز', 'ServiceID': 'خدمت',
        'ContractID': 'قرارداد', 'RefID': 'کد ارجاع سها', 'EmdadCheck': 'بررسی امداد',
        'CorporateContractServiceID': 'سرویس قرارداد', 'UserTariff': 'تعرفه کاربر',
        'EMS': 'کیس حاد', 'Level': 'سطح مشاور', 'CenterAdminID': 'مدیر مرکز',
        'SupervisorID': 'ناظر', 'AcceptorID': 'مشاور', 'AcceptorFee': 'حق‌الزحمه مشاور',
        'SecretaryFee': 'حق دبیرخانه', 'AcceptorCodeName': 'کد پذیرنده',
        'AcceptorLevel': 'سطح پذیرنده', 'SupervisorFee': 'حق‌الزحمه ناظر',
        'CenterFee': 'سهم مرکز', 'AdminFee': 'سهم مدیریت',
        'CenterAdminConfirmUserID': 'تایید مدیر مرکز', 'CenterAdminConfirmDateTime': 'زمان تایید مدیر مرکز',
        'CenterTechConfirmUserID': 'تایید مسئول فنی', 'CenterTechConfirmDateTime': 'زمان تایید مسئول فنی',
        'OperatorConfirmUserID': 'تایید نظارت حرفه‌ای', 'OperatorConfirmDateTime': 'زمان تایید نظارت حرفه‌ای',
        'ProvinceSupervisorConfirmUserID': 'تایید ناظر استان', 'ProvinceSupervisorConfirmDateTime': 'زمان تایید ناظر استان',
        'SupervisorConfirmUserID': 'تایید ناظر کشور', 'SupervisorConfirmDateTime': 'زمان تایید ناظر کشور',
        'StartDate': 'تاریخ شروع', 'EndDate': 'تاریخ پایان', 'Weight': 'وزن خدمت',
        'BudgetUsed': 'مصرف سهمیه', 'BudgetReserved': 'رزرو سهمیه',
        'RejectedByUserID': 'ردکننده', 'RejectedAt': 'زمان رد', 'RejectedComment': 'دلیل رد',
    },
    'Users': {
        'id': 'شناسه', 'NID': 'کد ملی', 'DetailCode': 'کد تفصیلی', 'Username': 'نام کاربری',
        'MFA': 'رمز دوم', 'Name': 'نام', 'Family': 'نام خانوادگی', 'Father': 'نام پدر',
        'Gender': 'جنسیت', 'Birthday': 'تاریخ تولد', 'Religion': 'دین',
        'MarriageID': 'وضعیت تاهل', 'EducationID': 'تحصیلات', 'Mobile': 'موبایل',
        'Mobile2': 'موبایل دوم', 'AreaCode': 'پیش‌شماره', 'Phone': 'تلفن', 'Email': 'ایمیل',
        'CountryID': 'کشور', 'ProvinceID': 'استان', 'CityID': 'شهرستان', 'Address': 'آدرس',
        'ZipCode': 'کد پستی', 'SignupDate': 'تاریخ ثبت‌نام', 'LastLogin': 'آخرین ورود',
        'Confirm': 'تاییدشده', 'Blocked': 'مسدود', 'LastChangePass': 'آخرین تغییر رمز',
        'RegistrationMethod': 'روش ثبت‌نام', 'Checked': 'بررسی‌شده',
    },
    'UserRoles': {
        'id': 'شناسه', 'UserID': 'کاربر', 'RoleID': 'نقش', 'RoleOption': 'گزینه نقش',
        'Level': 'سطح', 'StartDate': 'تاریخ شروع', 'EndDate': 'تاریخ پایان',
        'Confirm': 'تاریخ تایید', 'AddedBy': 'ثبت‌کننده', 'IsSuspended': 'معلق',
        'SuspendedBy': 'معلق‌کننده', 'SuspendedAt': 'زمان تعلیق', 'SuspendedReason': 'دلیل تعلیق',
    },
    'Roles': {'id': 'شناسه', 'Title': 'عنوان نقش', 'CodeName': 'کد نقش'},
    'Centers': {
        'id': 'شناسه', 'CenterTitle': 'نام مرکز', 'IsEnabled': 'فعال', 'Address': 'آدرس',
        'Tel': 'تلفن', 'CatID': 'دسته', 'CityID': 'شهرستان', 'CityTitle': 'شهرستان',
        'ProvinceID': 'استان', 'ProvinceTitle': 'استان',
    },
    'Provinces': {'id': 'شناسه', 'Title': 'استان', 'API': 'کد API', 'DetailCode': 'کد تفصیلی'},
    'Cities': {'id': 'شناسه', 'ProvinceID': 'استان', 'Title': 'شهرستان', 'APICode': 'کد API'},
    'Services': {'id': 'شناسه', 'Name': 'نام خدمت', 'Short': 'نام کوتاه', 'SohaID': 'کد سها', 'Weight': 'وزن'},
    'Referrs': {
        'id': 'شناسه', 'RefID': 'کد ارجاع سها', 'UserID': 'کاربر', 'ServiceID': 'خدمت',
        'Description': 'توضیحات', 'Status': 'وضعیت', 'IsReferr': 'ارجاع‌شده',
        'ProvinceID': 'استان', 'CityID': 'شهرستان', 'CenterID': 'مرکز',
        'AcceptorID': 'مشاور پذیرنده', 'AdminReferrerID': 'معرف اداری',
        'CreationDate': 'تاریخ ایجاد', 'Type': 'نوع ارجاع',
    },
    'ReferrsRequest': {
        'id': 'شناسه', 'UserID': 'کاربر', 'Description': 'توضیحات', 'Status': 'وضعیت',
        'ProvinceID': 'استان', 'CityID': 'شهرستان', 'CenterID': 'مرکز',
        'AdminReferrerID': 'معرف اداری', 'CreationDate': 'تاریخ ثبت', 'EditionDate': 'آخرین ویرایش',
    },
    'ReferrFollowUps': {'id': 'شناسه', 'ReferrID': 'ارجاع', 'UserID': 'پیگیر', 'Comment': 'یادداشت', 'CreatedAt': 'تاریخ'},
    'EventReserves': {
        'id': 'شناسه', 'EventID': 'جلسه', 'UserID': 'کاربر', 'AcceptorID': 'مشاور', 'Date': 'تاریخ رزرو',
    },
    'EventsEms': {
        'id': 'شناسه', 'EventID': 'جلسه', 'SecretaryNID': 'کد ملی ثبت‌کننده',
        'EMSType': 'نوع مورد حاد', 'SuicidalFrom': 'عوامل خودکشی',
        'SuicidalRiskLevel': 'شدت خطر', 'PsychiatricDisorders': 'اختلالات روانپزشکی',
        'SocialFactors': 'عوامل اجتماعی', 'ProtectiveFactors': 'عوامل محافظ',
        'SuggestedActions': 'اقدامات پیشنهادی', 'ActionsTaken': 'اقدامات انجام‌شده',
        'FinancialAssistanceRequest': 'درخواست کمک مالی', 'Status': 'وضعیت',
        'DateTime': 'تاریخ ثبت', 'HadPaymentAmount': 'مبلغ پرداخت',
        'HadPaymentNo': 'شماره پرداخت', 'HadPaymentDate': 'تاریخ پرداخت',
        'HadPaymentDescription': 'توضیح پرداخت', 'HadPaymentStatus': 'وضعیت پرداخت',
        'HadPaymentRefID': 'کد رهگیری پرداخت', 'ConfirmedByUserID': 'تاییدکننده',
        'ConfirmedAt': 'زمان تایید', 'RejectedByUserID': 'ردکننده', 'RejectedAt': 'زمان رد',
    },
    'EventEmsComments': {'id': 'شناسه', 'EventEmsID': 'مورد حاد', 'UserID': 'کاربر', 'Comment': 'نظر', 'Date': 'تاریخ'},
    'Groups': {
        'id': 'شناسه', 'Type': 'نوع گروه', 'CorporateContractID': 'قرارداد', 'CenterID': 'مرکز',
        'AcceptorID': 'مشاور گروه', 'CreatorID': 'ایجادکننده', 'Tel': 'تلفن', 'Address': 'آدرس',
        'Status': 'وضعیت', 'CreateDate': 'تاریخ ایجاد', 'RejectedByUserID': 'ردکننده',
        'RejectedAt': 'زمان رد', 'RejectedReason': 'دلیل رد',
    },
    'GroupEvents': {
        'id': 'شناسه', 'GroupID': 'گروه', 'Topic': 'موضوع', 'Description': 'شرح',
        'StartDate': 'تاریخ شروع', 'EndDate': 'تاریخ پایان', 'SessionNumber': 'شماره جلسه',
        'AcceptorID': 'مشاور', 'AcceptorCodeName': 'کد پذیرنده', 'AcceptorLevel': 'سطح پذیرنده',
        'SupervisorID': 'ناظر', 'CenterAdminID': 'مدیر مرکز', 'AcceptorFee': 'حق‌الزحمه مشاور',
        'SecretaryFee': 'حق دبیرخانه', 'SupervisorFee': 'حق ناظر', 'CenterFee': 'سهم مرکز',
        'AdminFee': 'سهم مدیریت', 'ServiceID': 'خدمت', 'ContractID': 'قرارداد',
        'UserTariff': 'تعرفه کاربر', 'BudgetReserved': 'رزرو سهمیه', 'BudgetUsed': 'مصرف سهمیه',
        'Weight': 'وزن', 'CenterID': 'مرکز',
        'CenterAdminConfirmUserID': 'تایید مدیر مرکز', 'CenterAdminConfirmDateTime': 'زمان تایید مدیر مرکز',
        'CenterTechConfirmUserID': 'تایید مسئول فنی', 'CenterTechConfirmDateTime': 'زمان تایید مسئول فنی',
        'OperatorConfirmUserID': 'تایید نظارت حرفه‌ای', 'OperatorConfirmDateTime': 'زمان تایید نظارت حرفه‌ای',
        'ProvinceSupervisorConfirmUserID': 'تایید ناظر استان', 'ProvinceSupervisorConfirmDateTime': 'زمان تایید ناظر استان',
        'SupervisorConfirmUserID': 'تایید ناظر کشور', 'SupervisorConfirmDateTime': 'زمان تایید ناظر کشور',
        'RejectedByUserID': 'ردکننده', 'RejectedAt': 'زمان رد', 'RejectedComment': 'دلیل رد',
    },
    'GroupMembers': {'id': 'شناسه', 'UserID': 'عضو', 'NID': 'کد ملی', 'GroupID': 'گروه', 'RefID': 'کد ارجاع', 'DateTime': 'تاریخ عضویت'},
    'GroupEventMember': {
        'id': 'شناسه', 'UserID': 'حاضر', 'GroupID': 'گروه', 'GroupEventID': 'جلسه گروهی',
        'ServiceID': 'خدمت', 'TrackingCode': 'کد رهگیری', 'RefID': 'کد ارجاع', 'DateTime': 'تاریخ',
    },
    'Budget': {
        'Id': 'شناسه', 'Title': 'عنوان سهمیه', 'Type': 'نوع', 'Amount': 'سقف سهمیه',
        'Remained': 'مانده', 'Reserved': 'رزرو', 'StartDate': 'تاریخ شروع', 'EndDate': 'تاریخ پایان',
        'CreateTime': 'تاریخ ایجاد', 'Creator': 'ایجادکننده', 'AmountBefore': 'سهمیه قبل از اجرا',
        'Used': 'استفاده‌شده', 'Assigned': 'تخصیص‌یافته',
    },
    'BudgetProvince': {'Id': 'شناسه', 'BudgetId': 'سهمیه', 'ProvinceId': 'استان', 'Amount': 'سقف', 'Remained': 'مانده', 'Reserved': 'رزرو', 'CreateTime': 'تاریخ', 'Used': 'استفاده‌شده', 'Assigned': 'تخصیص', 'AmountBefore': 'قبل از اجرا'},
    'BudgetCity': {'Id': 'شناسه', 'BudgetId': 'سهمیه', 'CityId': 'شهرستان', 'Amount': 'سقف', 'Remained': 'مانده', 'Reserved': 'رزرو', 'CreateTime': 'تاریخ', 'Used': 'استفاده‌شده', 'Assigned': 'تخصیص', 'AmountBefore': 'قبل از اجرا'},
    'BudgetCenter': {'Id': 'شناسه', 'BudgetId': 'سهمیه', 'CenterId': 'مرکز', 'Amount': 'سقف', 'Remained': 'مانده', 'Reserved': 'رزرو', 'CreateTime': 'تاریخ', 'Used': 'استفاده‌شده', 'Assigned': 'تخصیص', 'AmountBefore': 'قبل از اجرا'},
    'SMS': {
        'id': 'شناسه', 'SmsSender': 'فرستنده', 'SmsReceiver': 'گیرنده', 'Number': 'شماره',
        'Message': 'متن', 'Response': 'پاسخ', 'Status': 'وضعیت', 'Efforts': 'تلاش‌ها',
        'UpdateTime': 'آخرین بروزرسانی', 'CreateTime': 'تاریخ ارسال',
    },
    'Messages': {
        'id': 'شناسه', 'FromUID': 'فرستنده', 'ToUID': 'گیرنده', 'Subject': 'موضوع',
        'Text': 'متن', 'TargetRole': 'نقش هدف', 'TargetProvinceID': 'استان هدف',
        'Timestamp': 'زمان', 'Read': 'زمان خواندن', 'Star': 'ستاره',
    },
    'Log': {
        'id': 'شناسه', 'uid': 'کاربر', 'Category': 'دسته', 'Description': 'توضیح',
        'Level': 'سطح', 'IP': 'IP', 'Timestamp': 'تاریخ',
    },
    'Sessions': {'id': 'شناسه', 'UserID': 'کاربر', 'IP': 'IP', 'Browser': 'مرورگر', 'DateTime': 'زمان ورود'},
    'ConsultantTax': {
        'id': 'شناسه', 'NID': 'کد ملی', 'Year': 'سال', 'Month': 'ماه', 'TaxAmount': 'مالیات (ریال)',
        'ExemptionMonths': 'ماه معافیت', 'MultiEmployerMonth': 'چند کارفرما (ماه)',
        'MultiEmployerYear': 'چند کارفرما (سال)', 'TotalPayment': 'حق‌الزحمه (ریال)',
        'CreatedByUserID': 'ثبت‌کننده', 'CreatedAt': 'تاریخ ثبت', 'UpdatedAt': 'آخرین ویرایش',
    },
    'ConsultantEducation': {
        'id': 'شناسه', 'UserID': 'کاربر', 'ConsultantNID': 'کد ملی مشاور', 'Field': 'رشته',
        'Orientation': 'گرایش', 'Grade': 'مدرک', 'Univesity': 'دانشگاه',
        'GraduationDate': 'سال فارغ‌التحصیلی', 'DateTime': 'تاریخ ثبت', 'File': 'فایل',
    },
    'ConsultantExperience': {
        'id': 'شناسه', 'UserID': 'کاربر', 'ConsultantNID': 'کد ملی مشاور', 'Institute': 'سازمان',
        'StartDate': 'از', 'EndDate': 'تا', 'Type': 'نوع همکاری', 'ProficiencyID': 'صلاحیت', 'File': 'فایل',
    },
    'ConsultantCourses': {
        'id': 'شناسه', 'UserID': 'کاربر', 'ConsultantNID': 'کد ملی مشاور', 'Title': 'عنوان دوره',
        'PassedHours': 'ساعت', 'GraduatedDate': 'سال', 'HostOrganization': 'برگزارکننده',
        'HoldingDate': 'تاریخ برگزاری', 'Professors': 'اساتید', 'File': 'فایل',
    },
    'InvitePersons': {
        'ID': 'شناسه', 'NID': 'کد ملی', 'Name': 'نام', 'Mobile': 'شماره اول', 'Phone': 'شماره دوم',
        'Description': 'توضیحات', 'Response': 'نتیجه', 'Status': 'وضعیت', 'GroupID': 'شناسه گروه',
        'GroupName': 'نام گروه', 'ProvinceID': 'استان', 'CityID': 'شهرستان', 'CenterID': 'مرکز',
        'CreateTime': 'تاریخ ثبت', 'UpdateTime': 'آخرین تغییر',
    },
    'EventPsychology': {
        'id': 'شناسه', 'EventID': 'جلسه', 'UserID': 'مراجع', 'AcceptorID': 'مشاور',
        'Job': 'شغل', 'Ethnicity': 'قومیت', 'Religion': 'مذهب', 'ReligiousBelief': 'میزان مذهبی بودن',
        'Children': 'تعداد فرزند', 'ResidenceQuality': 'وضعیت مسکن', 'SpouseInfo': 'اطلاعات همسر',
        'ChildrenInfo': 'اطلاعات فرزندان', 'ProblemStart': 'شروع مشکل', 'SpecificEvent': 'رویداد خاص',
        'ProblemDuration': 'مدت مشکل', 'ClinicalObservation': 'مشاهده بالینی', 'Appearance': 'ظاهر',
        'PhysicalCondition': 'وضعیت جسمی', 'PsychomotorStatus': 'وضعیت روانی-حرکتی',
        'InterviewAttitude': 'نگرش در مصاحبه', 'Mood': 'خلق', 'Affect': 'عاطفه', 'Speech': 'تکلم',
        'Perception': 'ادراک', 'ThoughtContent': 'محتوای فکر', 'ThoughtProcess': 'سیر فکر',
        'Consciousness': 'هوشیاری', 'Orientation': 'جهت‌یابی', 'Memory': 'حافظه',
        'Concentration': 'تمرکز', 'Intelligence': 'هوش', 'Judgment': 'قضاوت', 'Insight': 'بینش',
        'MedicalHistory': 'سابقه پزشکی', 'FamilyHistory': 'سابقه خانوادگی',
        'FamilyRelationships': 'روابط خانوادگی', 'ParentsMarriageHistory': 'ازدواج والدین',
        'FamilyMedicalHistory': 'سابقه پزشکی خانواده', 'EvolutionaryHistory': 'تاریخچه تکاملی',
        'SchoolAdaptability': 'سازگاری مدرسه', 'PeerRelationships': 'روابط همسالان',
        'DatingHistory': 'سابقه دوستی', 'Strengths': 'نقاط قوت', 'Interests': 'علایق',
        'SocialSupport': 'حمایت اجتماعی', 'WelfareResources': 'منابع حمایتی',
        'Expectations': 'انتظارات', 'Feelings': 'احساسات', 'Disorder': 'اختلال',
        'TherapyMethods': 'روش‌های درمان', 'SupportReason': 'دلیل حمایت',
        'EmploymentStatus': 'وضعیت اشتغال', 'EducationLevel': 'سطح تحصیلات',
        'SuicideAttemptCount': 'تعداد اقدام به خودکشی', 'SuicideMethod': 'روش خودکشی',
        'DateTime': 'تاریخ ثبت',
    },
    'EventChildPsychology': {
        'id': 'شناسه', 'EventID': 'جلسه', 'Status': 'حوزه مشاهده', 'Visible': 'مشاهده ظاهری',
        'Atefe': 'عاطفه', 'LangMind': 'زبان ذهنی', 'Judge': 'قضاوت', 'Shenakht': 'شناخت',
        'ADHD': 'بیش‌فعالی', 'DiffSocial': 'مشکل اجتماعی', 'DiffEdu': 'مشکل تحصیلی',
        'Description': 'شرح', 'Age': 'سن', 'DateTime': 'تاریخ',
    },
    'EventNeuroFeedback': {
        'id': 'شناسه', 'EventID': 'جلسه', 'Protocol': 'پروتکل', 'Target': 'هدف درمان',
        'Visible': 'مشاهدات', 'Action': 'اقدام', 'Changed': 'تغییرات',
        'EzterabOld': 'آزمون‌پذیری قبل', 'EzterabNew': 'آزمون‌پذیری بعد',
        'AfsorOld': 'افسردگی قبل', 'AfsorNew': 'افسردگی بعد',
        'SleepProblemOld': 'مشکل خواب قبل', 'SleepProblemNew': 'مشکل خواب بعد',
        'FocusOld': 'تمرکز قبل', 'FocusNew': 'تمرکز بعد',
        'EnergyOld': 'انرژی قبل', 'EnergyNew': 'انرژی بعد', 'Other': 'سایر', 'DateTime': 'تاریخ',
    },
    'EventHeadMap': {'id': 'شناسه', 'EventID': 'جلسه', 'FileID': 'فایل', 'Description': 'توصیف', 'DateTime': 'تاریخ'},
    'EventMedicine': {'id': 'شناسه', 'EventID': 'جلسه', 'Medicine': 'دارو', 'DateTime': 'تاریخ'},
    'EventComments': {'id': 'شناسه', 'EventID': 'جلسه', 'ConsultantNID': 'مشاور', 'Comment': 'یادداشت', 'DateTime': 'تاریخ'},
    'EventQuizzes': {'id': 'شناسه', 'EventID': 'جلسه', 'Topic': 'موضوع', 'Description': 'شرح', 'Date': 'تاریخ'},
    'EventPersonal': {'id': 'شناسه', 'EventID': 'جلسه', 'Topic': 'موضوع', 'Description': 'شرح', 'DateTime': 'تاریخ'},
    'EventReferrs': {'id': 'شناسه', 'EventID': 'جلسه', 'UserID': 'مراجع', 'AcceptorID': 'مشاور گیرنده', 'ReferrerID': 'ارجاع‌دهنده', 'StartDate': 'تاریخ جلسه', 'DateTime': 'تاریخ ثبت'},
    'EventDisorders': {'id': 'شناسه', 'EventID': 'جلسه', 'DisordersID': 'اختلال'},
    'Incomes': {'id': 'شناسه', 'CenterID': 'مرکز', 'UserID': 'کاربر', 'EventID': 'جلسه', 'Type': 'نوع', 'Title': 'عنوان', 'Fee': 'مبلغ', 'IncomeDate': 'تاریخ درآمد', 'DateTime': 'تاریخ ثبت', 'Description': 'توضیحات', 'FileID': 'فایل'},
    'Expenses': {'id': 'شناسه', 'CenterID': 'مرکز', 'UserID': 'کاربر', 'Category': 'دسته', 'Type': 'نوع', 'Title': 'عنوان', 'PayTo': 'پرداخت به', 'PayType': 'نوع پرداخت', 'PayID': 'شناسه پرداخت', 'Fee': 'مبلغ', 'PayDate': 'تاریخ پرداخت', 'DateTime': 'تاریخ ثبت', 'Description': 'توضیحات', 'FileID': 'فایل'},
    'Files': {'id': 'شناسه', 'UserNID': 'کد ملی کاربر', 'Name': 'نام فایل', 'Location': 'مسیر', 'UploadDateTime': 'تاریخ بارگذاری'},
    'SpecialOccasions': {'id': 'شناسه', 'Title': 'عنوان', 'ImagePath': 'تصویر', 'DisplayDate': 'تاریخ نمایش', 'IsActive': 'فعال', 'CreatedByUserID': 'ایجادکننده', 'CreatedAt': 'تاریخ ایجاد', 'UpdatedAt': 'آخرین ویرایش'},
    'CorporateContracts': {'id': 'شناسه', 'CorporateCustomerID': 'مشتری سازمانی', 'AppDefault': 'پیش‌فرض اپ', 'StartDate': 'شروع', 'EndDate': 'پایان', 'Detect': 'روش شناسایی', 'Remove': 'حذف‌شده'},
    'CorporateContractServices': {
        'id': 'شناسه', 'CorporateContractID': 'قرارداد', 'ServiceID': 'خدمت', 'UserTariff': 'تعرفه کاربر',
        'ConsultantLevel1': 'حق مشاور پایه', 'ConsultantLevel2': 'حق مشاور ارشد',
        'ConsultantLevel3': 'حق مشاور متخصص', 'ConsultantLevel4': 'حق مشاور خبره',
        'ConsultantLevel5': 'حق مشاور ممتاز', 'ConsultantDR': 'حق دکتر', 'SecretaryFee': 'حق دبیرخانه',
        'SupervisorFee': 'حق ناظر', 'CenterFee': 'سهم مرکز', 'AdminFee': 'سهم مدیریت',
    },
    'CorporateCustomers': {'id': 'شناسه', 'Title': 'نام سازمان', 'Discount': 'تخفیف', 'Phone': 'تلفن'},
    'CareerCounseling': {
        'id': 'شناسه', 'RequestStatus': 'وضعیت درخواست', 'ProvinceID': 'استان', 'Province': 'استان (متن)',
        'Office': 'اداره', 'ApplicantNID': 'کد ملی متقاضی', 'ApplicantName': 'نام متقاضی',
        'ApplicantMobile': 'موبایل', 'ApplicantGender': 'جنسیت', 'TargetGroup': 'گروه هدف',
        'ApplicationDate': 'تاریخ درخواست', 'ConsultationDate': 'تاریخ مشاوره',
        'InstituteProvinceID': 'استان موسسه', 'InstituteProvince': 'استان موسسه (متن)',
        'Institute': 'موسسه', 'InstituteUniqueID': 'کد موسسه', 'ConsultantID': 'مشاور',
        'Status': 'وضعیت', 'HOLLAND': 'هالند', 'GARDNER': 'گاردنر', 'MBTI': 'MBTI',
        'MILON': 'میون', 'CreateDate': 'تاریخ ثبت', 'AgentID': 'کارشناس',
        'BudgetReserved': 'رزرو سهمیه', 'BudgetUsed': 'مصرف سهمیه', 'Weight': 'وزن',
    },
    'Settings': {'Name': 'کلید', 'Value': 'مقدار'},
    'ApiReports': {'id': 'شناسه', 'Type': 'نوع', 'Data': 'داده', 'Status': 'وضعیت', 'Response': 'پاسخ', 'Efforts': 'تلاش‌ها', 'CreateTime': 'ایجاد', 'UpdateTime': 'بروزرسانی'},
    'ApiStates': {'id': 'شناسه', 'city': 'شهر', 'province': 'استان', 'provinceID': 'کد استان'},
    'ApiTokens': {'id': 'شناسه', 'Token': 'توکن', 'CreateTime': 'ایجاد'},
    'CenterBankAccount': {'id': 'شناسه', 'CenterID': 'مرکز', 'UserID': 'کاربر', 'BankName': 'بانک', 'AccountNo': 'شماره حساب', 'Sheba': 'شبا', 'CardNo': 'شماره کارت', 'OwnerName': 'صاحب حساب'},
    'Helps': {'id': 'شناسه', 'RoleID': 'نقش', 'File_1': 'فایل ۱', 'File_2': 'فایل ۲', 'File_3': 'فایل ۳'},
    'JobsList': {'id': 'شناسه', 'Title': 'شغل', 'HaiatID': 'کد هیات'},
    'Education': {'id': 'شناسه', 'Name': 'مدرک'},
    'Marriage': {'id': 'شناسه', 'Name': 'وضعیت'},
    'Religion': {'id': 'شناسه', 'Name': 'دین'},
    'Disorders': {'id': 'شناسه', 'Name': 'نام اختلال', 'DisordersID': 'والد', 'OrderSort': 'ترتیب', 'Code': 'کد'},
    'ConsultScope': {'id': 'شناسه', 'Title': 'عنوان'},
    'CenterCategories': {'id': 'شناسه', 'Title': 'عنوان'},
    'CenterEquipments': {'id': 'شناسه', 'CenterID': 'مرکز', 'UserID': 'کاربر', 'ItemID': 'قلم', 'Count': 'تعداد', 'Description': 'توضیحات', 'DateTime': 'تاریخ'},
    'EquipmentItems': {'id': 'شناسه', 'Title': 'عنوان'},
    'ConsultantHistory': {'id': 'شناسه', 'UserID': 'کاربر', 'FileID': 'فایل', 'StartDate': 'شروع', 'EndDate': 'پایان', 'DateTime': 'تاریخ'},
    'ConsultantTeachingExperience': {'id': 'شناسه', 'UserID': 'کاربر', 'ProvinceID': 'استان', 'CityID': 'شهرستان', 'Institute': 'سازمان', 'StartDate': 'از', 'EndDate': 'تا', 'File': 'فایل'},
    'Notifications': {'id': 'شناسه', 'UserID': 'کاربر', 'Title': 'عنوان', 'Text': 'متن', 'IsRead': 'خوانده‌شده', 'DateTime': 'تاریخ'},
    'NotificationsQueue': {'id': 'شناسه', 'UserID': 'کاربر', 'Title': 'عنوان', 'Text': 'متن', 'DateTime': 'تاریخ'},
    'UserTicket': {'id': 'شناسه', 'UserID': 'کاربر', 'Title': 'عنوان', 'Status': 'وضعیت', 'CreateTime': 'تاریخ ثبت'},
    'UserMFA': {'id': 'شناسه', 'UserID': 'کاربر', 'Type': 'نوع', 'DateTime': 'تاریخ'},
    'UserPasskeys': {'id': 'شناسه', 'UserID': 'کاربر', 'Name': 'نام', 'DateTime': 'تاریخ'},
    '_fix_endrefer': {'id': 'شناسه', 'EventID': 'جلسه', 'RefID': 'کد ارجاع'},
}

# برچسب ستون‌های عمومی که همه‌جا یکسان‌اند
GENERIC_COL_LABELS = {
    'id': 'شناسه', 'Id': 'شناسه', 'ID': 'شناسه', 'UserID': 'کاربر', 'UserNID': 'کد ملی کاربر',
    'NID': 'کد ملی', 'CenterID': 'مرکز', 'ProvinceID': 'استان', 'CityID': 'شهرستان',
    'ServiceID': 'خدمت', 'RoleID': 'نقش', 'EventID': 'جلسه', 'GroupID': 'گروه',
    'CreateTime': 'تاریخ ایجاد', 'DateTime': 'تاریخ', 'CreatedAt': 'تاریخ ایجاد',
    'UpdatedAt': 'آخرین ویرایش', 'Status': 'وضعیت', 'Type': 'نوع', 'Title': 'عنوان',
    'Name': 'نام', 'Description': 'توضیحات', 'File': 'فایل', 'FileID': 'فایل',
    'StartDate': 'تاریخ شروع', 'EndDate': 'تاریخ پایان', 'Level': 'سطح', 'IP': 'IP',
    'Mobile': 'موبایل', 'Comment': 'یادداشت', 'Text': 'متن', 'Count': 'تعداد',
    'AcceptorID': 'مشاور', 'Creator': 'ایجادکننده', 'CreatorID': 'ایجادکننده', 'Weight': 'وزن',
    'Fee': 'مبلغ', 'Amount': 'مبلغ', 'Tel': 'تلفن', 'Phone': 'تلفن', 'Email': 'ایمیل',
    'RefID': 'کد ارجاع', 'TrackingCode': 'کد رهگیری', 'EducationID': 'تحصیلات',
    'MarriageID': 'وضعیت تاهل', 'Gender': 'جنسیت', 'Birthday': 'تاریخ تولد',
    'ContractID': 'قرارداد', 'CorporateContractID': 'قرارداد', 'IsActive': 'فعال',
    'IsEnabled': 'فعال', 'ConsultantID': 'مشاور', 'AdminReferrerID': 'معرف اداری',
    'SupervisorID': 'ناظر', 'CenterAdminID': 'مدیر مرکز', 'DisordersID': 'اختلال',
    'GroupEventID': 'جلسه گروهی', 'EventEmsID': 'مورد حاد', 'ReferrerID': 'ارجاع‌دهنده',
    'ConfirmedByUserID': 'تاییدکننده', 'RejectedByUserID': 'ردکننده', 'Uid': 'کاربر',
}

# ----------------------------------------------------------------------
# کلیدهای خارجی: table.col → {'parent': جدول والد, 'col': ستون اتصال (پیش‌فرض pk),
#   'by': 'id'|'nid', 'label': ستون(های) نمایش والد}
# ----------------------------------------------------------------------
USER = {'parent': 'Users', 'label': ['Name', 'Family']}
FK = {
    # Events
    'Events.UserID': USER, 'Events.AcceptorID': USER, 'Events.CenterAdminID': USER,
    'Events.SupervisorID': USER, 'Events.CenterAdminConfirmUserID': USER,
    'Events.CenterTechConfirmUserID': USER, 'Events.OperatorConfirmUserID': USER,
    'Events.ProvinceSupervisorConfirmUserID': USER, 'Events.SupervisorConfirmUserID': USER,
    'Events.RejectedByUserID': USER, 'Events.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'Events.ServiceID': {'parent': 'Services', 'label': ['Name']},
    'Events.ContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'Events.NID': {'parent': 'Users', 'by': 'nid', 'label': ['Name', 'Family']},
    # EventReserves / EventReferrs
    'EventReserves.EventID': {'parent': 'Events', 'label': ['id']},
    'EventReserves.UserID': USER, 'EventReserves.AcceptorID': USER,
    'EventReferrs.EventID': {'parent': 'Events', 'label': ['id']},
    'EventReferrs.UserID': USER, 'EventReferrs.AcceptorID': USER, 'EventReferrs.ReferrerID': USER,
    # EventsEms
    'EventsEms.EventID': {'parent': 'Events', 'label': ['id']},
    'EventsEms.SecretaryNID': {'parent': 'Users', 'by': 'nid', 'label': ['Name', 'Family']},
    'EventsEms.ConfirmedByUserID': USER, 'EventsEms.RejectedByUserID': USER,
    'EventEmsComments.EventEmsID': {'parent': 'EventsEms', 'label': ['id']},
    'EventEmsComments.UserID': USER,
    # بقیه فرزندان Events
    'EventPsychology.EventID': {'parent': 'Events', 'label': ['id']},
    'EventPsychology.UserID': USER, 'EventPsychology.AcceptorID': USER,
    'EventChildPsychology.EventID': {'parent': 'Events', 'label': ['id']},
    'EventNeuroFeedback.EventID': {'parent': 'Events', 'label': ['id']},
    'EventHeadMap.EventID': {'parent': 'Events', 'label': ['id']},
    'EventHeadMap.FileID': {'parent': 'Files', 'label': ['Name']},
    'EventMedicine.EventID': {'parent': 'Events', 'label': ['id']},
    'EventComments.EventID': {'parent': 'Events', 'label': ['id']},
    'EventQuizzes.EventID': {'parent': 'Events', 'label': ['id']},
    'EventPersonal.EventID': {'parent': 'Events', 'label': ['id']},
    'EventDisorders.EventID': {'parent': 'Events', 'label': ['id']},
    'EventDisorders.DisordersID': {'parent': 'Disorders', 'label': ['Name']},
    # Users
    'Users.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'Users.CityID': {'parent': 'Cities', 'label': ['Title']},
    'Users.MarriageID': {'parent': 'Marriage', 'label': ['Name']},
    'Users.EducationID': {'parent': 'Education', 'label': ['Name']},
    # UserRoles
    'UserRoles.UserID': USER, 'UserRoles.RoleID': {'parent': 'Roles', 'label': ['Title']},
    'UserRoles.AddedBy': USER, 'UserRoles.SuspendedBy': USER,
    # مراکز و جغرافیا
    'Centers.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'Centers.CityID': {'parent': 'Cities', 'label': ['Title']},
    'Centers.CatID': {'parent': 'CenterCategories', 'label': ['Title']},
    'Cities.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'ApiStates.provinceID': {'parent': 'Provinces', 'label': ['Title']},
    # Referrs
    'Referrs.UserID': USER, 'Referrs.ServiceID': {'parent': 'Services', 'label': ['Name'], 'via': 'soha'},
    'Referrs.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'Referrs.CityID': {'parent': 'Cities', 'label': ['Title']},
    'Referrs.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'Referrs.AcceptorID': USER, 'Referrs.AdminReferrerID': USER,
    'ReferrFollowUps.ReferrID': {'parent': 'Referrs', 'label': ['id']},
    'ReferrFollowUps.UserID': USER,
    'ReferrsRequest.UserID': USER, 'ReferrsRequest.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'ReferrsRequest.CityID': {'parent': 'Cities', 'label': ['Title']},
    'ReferrsRequest.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'ReferrsRequest.AdminReferrerID': USER,
    # گروه‌ها
    'Groups.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'Groups.AcceptorID': USER, 'Groups.CreatorID': USER,
    'Groups.CorporateContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'Groups.RejectedByUserID': USER,
    'GroupEvents.GroupID': {'parent': 'Groups', 'label': ['id']},
    'GroupEvents.AcceptorID': USER, 'GroupEvents.SupervisorID': USER, 'GroupEvents.CenterAdminID': USER,
    'GroupEvents.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'GroupEvents.ServiceID': {'parent': 'Services', 'label': ['Name']},
    'GroupEvents.ContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'GroupEvents.CenterAdminConfirmUserID': USER, 'GroupEvents.CenterTechConfirmUserID': USER,
    'GroupEvents.OperatorConfirmUserID': USER, 'GroupEvents.ProvinceSupervisorConfirmUserID': USER,
    'GroupEvents.SupervisorConfirmUserID': USER, 'GroupEvents.RejectedByUserID': USER,
    'GroupMembers.UserID': USER, 'GroupMembers.GroupID': {'parent': 'Groups', 'label': ['id']},
    'GroupEventMember.UserID': USER, 'GroupEventMember.GroupID': {'parent': 'Groups', 'label': ['id']},
    'GroupEventMember.GroupEventID': {'parent': 'GroupEvents', 'label': ['id']},
    'GroupEventMember.ServiceID': {'parent': 'Services', 'label': ['Name']},
    'GroupEventReserves.GroupID': {'parent': 'Groups', 'label': ['id']},
    'GroupEventReserves.AcceptorID': USER,
    # بودجه
    'Budget.Creator': USER, 'BudgetProvince.BudgetId': {'parent': 'Budget', 'label': ['Title']},
    'BudgetProvince.ProvinceId': {'parent': 'Provinces', 'label': ['Title']},
    'BudgetCity.BudgetId': {'parent': 'Budget', 'label': ['Title']},
    'BudgetCity.CityId': {'parent': 'Cities', 'label': ['Title']},
    'BudgetCenter.BudgetId': {'parent': 'Budget', 'label': ['Title']},
    'BudgetCenter.CenterId': {'parent': 'Centers', 'label': ['CenterTitle']},
    # مالی
    'Incomes.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'Incomes.UserID': USER, 'Incomes.EventID': {'parent': 'Events', 'label': ['id']},
    'Incomes.FileID': {'parent': 'Files', 'label': ['Name']},
    'Expenses.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'Expenses.UserID': USER, 'Expenses.FileID': {'parent': 'Files', 'label': ['Name']},
    # پیامک/پیام/لاگ/نشست
    'SMS.SmsSender': USER, 'SMS.SmsReceiver': USER,
    'Messages.FromUID': USER, 'Messages.ToUID': USER,
    'Messages.TargetProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'Messages.FileID': {'parent': 'Files', 'label': ['Name']},
    'Log.uid': USER, 'Sessions.UserID': USER,
    # مشاوران
    'ConsultantTax.CreatedByUserID': USER,
    'ConsultantEducation.UserID': USER, 'ConsultantExperience.UserID': USER,
    'ConsultantCourses.UserID': USER, 'ConsultantHistory.UserID': USER,
    'ConsultantTeachingExperience.UserID': USER,
    'ConsultantTeachingExperience.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'ConsultantTeachingExperience.CityID': {'parent': 'Cities', 'label': ['Title']},
    'CareerCounseling.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'CareerCounseling.InstituteProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'CareerCounseling.ConsultantID': USER, 'CareerCounseling.AgentID': USER,
    # قراردادها
    'CorporateContracts.CorporateCustomerID': {'parent': 'CorporateCustomers', 'label': ['Title']},
    'CorporateContractServices.CorporateContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'CorporateContractServices.ServiceID': {'parent': 'Services', 'label': ['Name']},
    'CorporateContractCoupons.CorporateContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'CorporateContractCoupons.UserID': USER,
    'CorporateContractNIDs.CorporateContractID': {'parent': 'CorporateContracts', 'label': ['id']},
    'CorporateContractNIDs.UserID': USER,
    # متفرقه
    'InvitePersons.ProvinceID': {'parent': 'Provinces', 'label': ['Title']},
    'InvitePersons.CityID': {'parent': 'Cities', 'label': ['Title']},
    'InvitePersons.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'CenterBankAccount.UserID': USER,
    'CenterEquipments.CenterID': {'parent': 'Centers', 'label': ['CenterTitle']},
    'CenterEquipments.UserID': USER,
    'Helps.RoleID': {'parent': 'Roles', 'label': ['Title']},
    'SpecialOccasions.CreatedByUserID': USER,
    'UserTicket.UserID': USER, 'UserMFA.UserID': USER, 'UserPasskeys.UserID': USER,
    'Files.UserNID': {'parent': 'Users', 'by': 'nid', 'label': ['Name', 'Family']},
}

# ----------------------------------------------------------------------
# دیکشنری‌های استاتیک مقادیر
# ----------------------------------------------------------------------
EDU_GRADES = ['حوزوی', 'بی‌سواد', 'ابتدایی', 'متوسطه اول', 'متوسطه', 'دیپلم',
              'فوق‌دیپلم', 'لیسانس', 'فوق‌لیسانس', 'دکتری']
CONSULTANT_LEVELS = {1: 'مشاور پایه', 2: 'مشاور ارشد', 3: 'مشاور متخصص',
                     4: 'مشاور خبره', 5: 'مشاور ممتاز'}
CONFIRM_STAGES = [
    ('CenterAdminConfirmUserID', 'CenterAdminConfirmDateTime', 'مدیر مرکز'),
    ('CenterTechConfirmUserID', 'CenterTechConfirmDateTime', 'مسئول فنی'),
    ('OperatorConfirmUserID', 'OperatorConfirmDateTime', 'نظارت حرفه‌ای'),
    ('ProvinceSupervisorConfirmUserID', 'ProvinceSupervisorConfirmDateTime', 'ناظر استان'),
    ('SupervisorConfirmUserID', 'SupervisorConfirmDateTime', 'ناظر کشور'),
]

ENUMS = {
    ('Events', 'EMS'): 'bit', ('Events', 'EmdadCheck'): 'bit',
    ('Events', 'Level'): 'level', ('Events', 'AcceptorLevel'): 'level',
    ('Events', 'BudgetUsed'): 'yn01', ('Events', 'BudgetReserved'): 'yn01',
    ('GroupEvents', 'AcceptorLevel'): 'level',
    ('EventsEms', 'SuicidalRiskLevel'): {
        'low': 'کم', 'medium': 'متوسط', 'high': 'بالا', 'norisk': 'بدون خطر'},
    ('EventsEms', 'Status'): {
        'Pending': 'در انتظار بررسی', 'inProgress': 'در حال بررسی',
        'Done': 'تایید شده', 'Reject': 'رد شده'},
    ('EventsEms', 'FinancialAssistanceRequest'): 'yn01',
    ('Referrs', 'Status'): {'Pending': 'در انتظار', 'inProgress': 'در جریان', 'Done': 'انجام شده'},
    ('Referrs', 'Type'): {'soha': 'سها', 'inPerson': 'حضوری'},
    ('ReferrsRequest', 'Status'): {'Pending': 'در انتظار', 'inProgress': 'در جریان', 'Done': 'انجام شده'},
    ('Groups', 'Type'): {'counseling': 'مشاوره‌ای', 'educational': 'آموزشی'},
    ('Groups', 'Status'): {'pending': 'در انتظار تایید', 'confirmed': 'تایید شده',
                           'rejected': 'رد شده', 'draft': 'پیش‌نویس'},
    ('InvitePersons', 'Status'): {'ارجاع شده': 'ارجاع شده', 'در حال بررسی': 'در حال بررسی',
                                  'اتمام بررسی': 'اتمام بررسی'},
    ('SMS', 'Status'): {'Pending': 'در صف', 'Failed': 'ناموفق', 'Success': 'موفق'},
    ('ApiReports', 'Status'): {'Pending': 'در صف', 'Failed': 'ناموفق', 'Success': 'موفق', 'Error': 'خطا'},
    ('Budget', 'Type'): {'Main': 'خدمات فردی', 'Group': 'خدمات گروهی', 'Job': 'مشاوره شغلی'},
    ('CareerCounseling', 'Status'): {'مشاهده نشده': 'مشاهده نشده', 'در حال انجام': 'در حال انجام', 'ثبت شده': 'ثبت شده'},
    ('CareerCounseling', 'RequestStatus'): {'درجریان': 'در جریان'},
    ('Users', 'Gender'): {'male': 'مرد', 'female': 'زن'},
    ('Users', 'Confirm'): 'yn01', ('Users', 'Blocked'): 'yn01', ('Users', 'Checked'): 'yn01',
    ('Users', 'RegistrationMethod'): {'Web': 'وب', 'Internal': 'داخلی', 'API': 'API', 'Developer': 'توسعه‌دهنده'},
    ('Users', 'MFA'): {'None': 'غیرفعال', 'Authenticator': 'اپلیکیشن', 'SMS': 'پیامکی', 'Email': 'ایمیل', 'Passkey': 'کلید عبور'},
    ('UserRoles', 'Level'): 'level', ('UserRoles', 'IsSuspended'): 'yn01',
    ('Centers', 'IsEnabled'): 'yn01',
    ('ConsultantExperience', 'Type'): {'inperson': 'حضوری', 'online': 'آنلاین', 'phone': 'تلفنی', 'chat': 'چت'},
    ('CorporateContracts', 'Detect'): {'Always': 'همیشه', 'API': 'API', 'NID': 'کد ملی', 'Coupon': 'کد تخفیف'},
    ('Log', 'Level'): {0: 'اطلاع', 1: 'هشدار', 2: 'خطا', 3: 'بحرانی', 4: 'امنیتی', 5: 'ورود', 6: 'سیستم'},
    ('Messages', 'Star'): 'yn01',
    ('SpecialOccasions', 'IsActive'): 'yn01',
}

# ----------------------------------------------------------------------
# ستون‌های تاریخ هر جدول (برای فیلتر شمسی و نمایش)
# ----------------------------------------------------------------------
DATES = {
    'Events': ['StartDate', 'EndDate', 'CenterAdminConfirmDateTime', 'CenterTechConfirmDateTime',
               'OperatorConfirmDateTime', 'ProvinceSupervisorConfirmDateTime', 'SupervisorConfirmDateTime',
               'RejectedAt'],
    'GroupEvents': ['StartDate', 'EndDate', 'CenterAdminConfirmDateTime', 'CenterTechConfirmDateTime',
                    'OperatorConfirmDateTime', 'ProvinceSupervisorConfirmDateTime',
                    'SupervisorConfirmDateTime', 'RejectedAt'],
    'EventReserves': ['Date'],
    'Referrs': ['CreationDate'], 'ReferrsRequest': ['CreationDate', 'EditionDate'],
    'ReferrFollowUps': ['CreatedAt'],
    'Users': ['SignupDate', 'LastLogin', 'Birthday', 'LastChangePass'],
    'UserRoles': ['StartDate', 'EndDate', 'Confirm', 'SuspendedAt'],
    'Groups': ['CreateDate', 'RejectedAt'], 'GroupMembers': ['DateTime'],
    'GroupEventMember': ['DateTime'], 'GroupEventReserves': ['StartDate'],
    'EventsEms': ['DateTime', 'ConfirmedAt', 'RejectedAt', 'HadPaymentDate'],
    'EventEmsComments': ['Date'],
    'EventPsychology': ['DateTime'], 'EventChildPsychology': ['DateTime'],
    'EventNeuroFeedback': ['DateTime'], 'EventHeadMap': ['DateTime'],
    'EventMedicine': ['DateTime'], 'EventComments': ['DateTime'],
    'EventQuizzes': ['Date'], 'EventPersonal': ['DateTime'],
    'SMS': ['CreateTime', 'UpdateTime'], 'Messages': ['Timestamp', 'Read'],
    'Log': ['Timestamp'], 'Sessions': ['DateTime'],
    'Budget': ['StartDate', 'EndDate', 'CreateTime'],
    'BudgetProvince': ['CreateTime'], 'BudgetCity': ['CreateTime'], 'BudgetCenter': ['CreateTime'],
    'Incomes': ['IncomeDate', 'DateTime'], 'Expenses': ['PayDate', 'DateTime'],
    'ConsultantTax': ['CreatedAt', 'UpdatedAt'],
    'ConsultantEducation': ['DateTime'], 'ConsultantCourses': ['HoldingDate'],
    'InvitePersons': ['CreateTime', 'UpdateTime'],
    'ApiReports': ['CreateTime', 'UpdateTime'],
    'Files': ['UploadDateTime'], 'SpecialOccasions': ['DisplayDate', 'CreatedAt', 'UpdatedAt'],
    'CorporateContracts': ['StartDate', 'EndDate'],
    'CareerCounseling': ['ApplicationDate', 'ConsultationDate', 'CreateDate', 'ReferralTime', 'CompletionTime'],
    'UserTicket': ['CreateTime'], 'UserMFA': ['DateTime'], 'UserPasskeys': ['DateTime'],
    'ConsultantHistory': ['StartDate', 'EndDate', 'DateTime'],
}

# ستون تاریخ «اصلی» هر جدول برای فیلتر سریع بازه زمانی
PRIMARY_DATE = {
    'Events': 'StartDate', 'GroupEvents': 'StartDate', 'EventReserves': 'Date',
    'Referrs': 'CreationDate', 'ReferrsRequest': 'CreationDate', 'Users': 'SignupDate',
    'UserRoles': 'StartDate', 'Groups': 'CreateDate', 'EventsEms': 'DateTime',
    'SMS': 'CreateTime', 'Log': 'Timestamp', 'Messages': 'Timestamp', 'Sessions': 'DateTime',
    'Incomes': 'IncomeDate', 'Expenses': 'PayDate', 'ConsultantTax': 'CreatedAt',
    'InvitePersons': 'CreateTime', 'ApiReports': 'CreateTime', 'CareerCounseling': 'ApplicationDate',
    'ReferrFollowUps': 'CreatedAt', 'GroupEventMember': 'DateTime', 'GroupMembers': 'DateTime',
}

# ----------------------------------------------------------------------
# ستون‌های محرمانه — هرگز نمایش/خروجی داده نمی‌شوند
# ----------------------------------------------------------------------
SENSITIVE_PATTERNS = ('password', 'passwd', 'secret', 'privatekey', 'credential',
                      'seed', 'signature')
SENSITIVE_COLS = {
    ('Users', 'Password'), ('Sessions', 'Key'), ('Messages', 'Delete'),
    ('ApiTokens', 'Token'),
}


def is_sensitive(table, col):
    lc = col.lower()
    if (table, col) in SENSITIVE_COLS:
        return True
    if lc in ('password', 'secret', 'token', 'privatekey', 'credentialid'):
        return True
    for p in SENSITIVE_PATTERNS:
        if p in lc and col not in ('TotalPayment',):
            return True
    return False


def col_label(table, col):
    """برچسب فارسی ستون؛ ترتیب: جدول → عمومی → نام اصلی"""
    t = COLS.get(table) or {}
    if col in t:
        return t[col]
    if col in GENERIC_COL_LABELS:
        return GENERIC_COL_LABELS[col]
    return col


def table_label(table):
    return (TABLES.get(table) or (table, ''))[0]


def table_desc(table):
    return (TABLES.get(table) or (table, ''))[1]


def dict_key(table, col):
    """کلید دیکشنری برای (جدول، ستون)؛ None یعنی ترجمه ندارد"""
    if (table, col) in ENUMS:
        return ENUMS[(table, col)]
    if col in ('Level',) and table in ('Events', 'UserRoles', 'GroupEvents'):
        return 'level'
    return None


def apply_static_dict(key, value):
    """ترجمه مقدار با دیکشنری استاتیک"""
    if value is None or value == '':
        return ''
    if key == 'bit':
        if isinstance(value, (bytes, bytearray)):
            value = value[-1] if value else 0
        try:
            return 'بله' if int(value) else 'خیر'
        except (ValueError, TypeError):
            return 'بله' if value else 'خیر'
    if key == 'yn01':
        try:
            return 'بله' if int(value) else 'خیر'
        except (ValueError, TypeError):
            return str(value)
    if key == 'level':
        try:
            return CONSULTANT_LEVELS.get(int(value), f'سطح {value}')
        except (ValueError, TypeError):
            return str(value)
    if isinstance(key, dict):
        if isinstance(value, (bytes, bytearray)):
            value = value[-1] if value else 0
        for k, v in key.items():
            try:
                if str(value).lower() == str(k).lower() or (
                        isinstance(k, int) and str(value) == str(k)):
                    return v
            except Exception:
                continue
        return str(value)
    return str(value)

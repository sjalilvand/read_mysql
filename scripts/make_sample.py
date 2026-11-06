# -*- coding: utf-8 -*-
"""ساخت بکاپ نمونه (همان ساختار دیتابیس واقعی راه زندگی) برای تست برنامه."""
import os
import random
import sys

random.seed(42)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'test', 'sample_real.sql')

L = []
def add(s): L.append(s)
def ins(table, cols, rows):
    for r in rows:
        vals = []
        for v in r:
            if v is None: vals.append('NULL')
            elif isinstance(v, (int, float)): vals.append(str(v))
            else:
                s = str(v).replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
                vals.append(f"'{s}'")
        add(f"INSERT INTO `{table}` (`" + "`,`".join(cols) + f"`) VALUES ({','.join(vals)});")

# ---------------- مراجع ثابت ----------------
PROV = [(1,'آذربایجان شرقی'),(4,'اصفهان'),(8,'تهران'),(9,'چهارمحال'),(11,'خراسان رضوی'),
        (14,'کرمانشاه'),(17,'فارس'),(23,'گیلان'),(29,'هرمزگان'),(30,'همدان')]
add("CREATE TABLE `Provinces` (`id` int NOT NULL, `Title` varchar(255) DEFAULT NULL, `API` int NOT NULL DEFAULT '0', `DetailCode` smallint DEFAULT NULL, PRIMARY KEY (`id`));")
ins('Provinces', ['id','Title','API','DetailCode'], [(i,t,10+i,9000+i) for i,t in PROV])

CITIES = [(301,8,'تهران'),(308,8,'قدس'),(127,4,'اصفهان'),(3,14,'کرمانشاه'),(647,30,'همدان'),
          (803,29,'بندرعباس'),(1035,17,'شیراز'),(201,11,'مشهد')]
add("CREATE TABLE `Cities` (`id` int NOT NULL, `ProvinceID` int NOT NULL, `Title` varchar(255) DEFAULT NULL, `APICode` bigint NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
ins('Cities', ['id','ProvinceID','Title','APICode'], [(i,p,t,2165063800+i) for i,p,t in CITIES])

add("CREATE TABLE `Centers` (`id` int NOT NULL, `CenterTitle` varchar(255) NOT NULL, `IsEnabled` tinyint NOT NULL DEFAULT '1', `Address` text, `Tel` varchar(255) DEFAULT NULL, `CatID` int DEFAULT NULL, `CityID` int NOT NULL, `CityTitle` varchar(255) NOT NULL, `ProvinceID` int NOT NULL, `ProvinceTitle` varchar(255) NOT NULL, PRIMARY KEY (`id`));")
CENTERS = [(1,'مدیریت کل کشور',0,301,'تهران',8,'تهران'),
           (18,'کلینیک اصفهان مرکزی',1,127,'اصفهان',4,'اصفهان'),
           (22,'اداره جنوب تهران',1,301,'تهران',8,'تهران'),
           (28,'کلینیک مشهد قدس',1,201,'مشهد',11,'خراسان رضوی'),
           (443,'مرکز همدان',1,647,'همدان',30,'همدان'),
           (695,'مرکز شیراز',1,1035,'شیراز',17,'فارس')]
ins('Centers', ['id','CenterTitle','IsEnabled','Address','Tel','CatID','CityID','CityTitle','ProvinceID','ProvinceTitle'],
    [(i,t,en,f'آدرس {t}','02112345678',1,c,ct,p,pt) for i,t,en,c,ct,p,pt in CENTERS])

SERVICES = [(1,'مشاوره فردی (حضوری)','فردی‌حضوری',5,1.0),(2,'مشاوره فردی (تلفنی)','فردی‌تلفنی',13,1.0),
            (3,'مشاوره فردی (در محل)','فردی‌درمحل',6,1.0),(4,'مشاوره روان‌درمانی','روان‌درمانی',11,1.5),
            (5,'مشاوره روانپزشکی','روانپزشکی',12,2.0),(6,'مشاوره گروهی','گروهی',7,0.5),
            (7,'آموزش گروهی','آموزش',8,0.5),(8,'آزمون روانسنجی','روانسنجی',9,1.0),
            (9,'موارد حاد (آسیب به خود)','موارد حاد',10,3.0),(10,'مشاوره روان‌درمانی (در محل)','درمانی‌درمحل',2,1.5),
            (11,'نوروفیدبک','نوروفیدبک',14,2.5),(12,'نقشه مغزی','نقشه مغزی',15,3.0)]
add("CREATE TABLE `Services` (`id` int NOT NULL, `Name` varchar(255) NOT NULL, `Short` varchar(255) NOT NULL, `SohaID` int NOT NULL, `Weight` decimal(10,1) NOT NULL DEFAULT '1.0', PRIMARY KEY (`id`));")
ins('Services', ['id','Name','Short','SohaID','Weight'], SERVICES)

add("CREATE TABLE `Education` (`id` int NOT NULL, `Name` varchar(255) DEFAULT NULL, PRIMARY KEY (`id`));")
ins('Education', ['id','Name'], [(1,'حوزوی'),(2,'بی سواد'),(3,'ابتدایی'),(4,'دیپلم'),(5,'فوق دیپلم'),(6,'لیسانس'),(7,'فوق لیسانس'),(8,'دکتری')])
add("CREATE TABLE `Marriage` (`id` int NOT NULL, `Name` varchar(255) DEFAULT NULL, PRIMARY KEY (`id`));")
ins('Marriage', ['id','Name'], [(1,'مجرد'),(2,'متاهل'),(3,'مطلقه'),(4,'همسرفوت شده'),(5,'متارکه'),(6,'نامشخص')])
add("CREATE TABLE `Roles` (`id` int NOT NULL, `Title` varchar(255) NOT NULL, `CodeName` varchar(255) NOT NULL, PRIMARY KEY (`id`));")
ins('Roles', ['id','Title','CodeName'], [(1,'برنامه‌نویس','developer'),(2,'مدیر کشور','admin'),(3,'نظارت حرفه‌ای','operator'),
    (4,'ناظر کشور','supervisor'),(5,'ناظر استان','province_supervisor'),(6,'مدیر مرکز','center_admin'),
    (7,'مسئول فنی','center_tech'),(8,'مشاور و روانشناس','adviser'),(9,'روانپزشک','psychiatrist'),(10,'پذیرش حضوری','secretary')])

# ---------------- کاربران ----------------
FIRST = ['محمد','زهرا','علی','فاطمه','رضا','مریم','حسین','سارا','امیر','نگار','مهدی','الهام']
FAM = ['احمدی','محمدی','رضایی','حسینی','کریمی','موسوی','صادقی','جعفری','علیمردانی','نوروزی']
add("CREATE TABLE `Users` (`id` int NOT NULL AUTO_INCREMENT, `NID` bigint(10) NOT NULL, `DetailCode` varchar(50) DEFAULT NULL, `Username` varchar(255) NOT NULL, `Password` varchar(255) NOT NULL, `MFA` enum('None','Authenticator','SMS','Email','Passkey') NOT NULL DEFAULT 'None', `Name` varchar(255) NOT NULL DEFAULT 'بی نام', `Family` varchar(255) NOT NULL DEFAULT 'بدون نام خانوادگی', `Father` varchar(255) NOT NULL DEFAULT '', `Gender` enum('male','female') DEFAULT NULL, `Birthday` date DEFAULT NULL, `Religion` varchar(255) NOT NULL DEFAULT '', `MarriageID` int DEFAULT '0', `EducationID` int DEFAULT NULL, `Mobile` bigint(11) NOT NULL, `Mobile2` bigint(11) DEFAULT NULL, `AreaCode` tinyint(3) DEFAULT NULL, `Phone` int(8) DEFAULT NULL, `Email` varchar(255) DEFAULT NULL, `Species` enum('Human') NOT NULL DEFAULT 'Human', `CountryID` int NOT NULL DEFAULT '117', `ProvinceID` int NOT NULL, `CityID` int NOT NULL DEFAULT '0', `Address` text, `ZipCode` bigint(10) DEFAULT NULL, `SignupDate` datetime NOT NULL, `LastLogin` datetime DEFAULT NULL, `Confirm` tinyint DEFAULT '0', `Blocked` tinyint(1) NOT NULL DEFAULT '0', `LastChangePass` date DEFAULT NULL, `RegistrationMethod` enum('Web','Internal','API','Developer') DEFAULT NULL, `Checked` tinyint(1) NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
users = []
uid = 10
for i in range(48):
    uid += 1
    gender = random.choice(['male','female'])
    first = random.choice(FIRST)
    fam = random.choice(FAM)
    prov = random.choice(PROV)[0]
    city = random.choice([c for c in CITIES if c[1] == prov] or CITIES)[0]
    signup = f"202{random.choice([4,4,5,5])}-{random.randint(1,12):02d}-{random.randint(1,28):02d} 09:00:00"
    lastlogin = f"2026-1{random.randint(0,1)}-{random.randint(1,28):02d} 10:00:00"
    # مشاوران ۱۰ نفر اول
    role_adv = i < 10
    nid = random.randint(1000000000, 9999999999)
    users.append({'id': uid, 'nid': nid, 'name': first, 'family': fam, 'gender': gender,
                  'prov': prov, 'city': city, 'adv': role_adv,
                  'mobile': random.randint(9100000000, 9999999999),
                  'signup': signup, 'last': lastlogin,
                  'marriage': random.randint(1,3), 'edu': random.randint(4,8)})
ins('Users', ['id','NID','Username','Password','MFA','Name','Family','Father','Gender','Birthday','Religion','MarriageID','EducationID','Mobile','ProvinceID','CityID','Address','SignupDate','LastLogin','Confirm','Blocked','RegistrationMethod'],
    [(u['id'], u['nid'], f'u{u["id"]}', '$2y$10$HASHED', 'None', u['name'], u['family'], 'پدر',
      u['gender'], '1995-05-04', '1', u['marriage'], u['edu'], u['mobile'], u['prov'], u['city'],
      'آدرس', u['signup'], u['last'], 1, 0, 'Web') for u in users])

add("CREATE TABLE `UserRoles` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `RoleID` int NOT NULL, `RoleOption` int NOT NULL DEFAULT '0', `Level` int NOT NULL DEFAULT '1', `StartDate` datetime NOT NULL, `EndDate` datetime DEFAULT NULL, `Confirm` datetime DEFAULT NULL, `AddedBy` int DEFAULT NULL, `IsSuspended` tinyint(1) NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
ur_rows = []
ur_id = 1
for u in users:
    role = 8 if u['adv'] else 10
    ur_rows.append((ur_id, u['id'], role, 0, random.randint(1,5), '2024-06-21 00:00:00', None, 0))
    ur_id += 1
ins('UserRoles', ['id','UserID','RoleID','RoleOption','Level','StartDate','EndDate','IsSuspended'], ur_rows)

# ---------------- جلسات ----------------
add("CREATE TABLE `Events` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `NID` bigint(10) NOT NULL, `TrackingCode` int DEFAULT NULL, `CenterID` int NOT NULL DEFAULT '0', `ServiceID` int NOT NULL, `ContractID` int NOT NULL, `RefID` bigint DEFAULT NULL, `EmdadCheck` bit(1) NOT NULL DEFAULT b'0', `CorporateContractServiceID` int NOT NULL, `UserTariff` int NOT NULL, `EMS` bit(1) NOT NULL DEFAULT b'0', `Level` int NOT NULL, `CenterAdminID` int NOT NULL, `SupervisorID` int NOT NULL, `AcceptorID` int NOT NULL, `AcceptorFee` int NOT NULL, `SecretaryFee` int NOT NULL DEFAULT '0', `AcceptorCodeName` varchar(100) NOT NULL, `AcceptorLevel` tinyint NOT NULL DEFAULT '1', `SupervisorFee` int NOT NULL, `CenterFee` int NOT NULL, `AdminFee` int NOT NULL, `CenterAdminConfirmUserID` int DEFAULT NULL, `CenterAdminConfirmDateTime` datetime DEFAULT NULL, `CenterTechConfirmUserID` int DEFAULT NULL, `CenterTechConfirmDateTime` datetime DEFAULT NULL, `OperatorConfirmUserID` int DEFAULT NULL, `OperatorConfirmDateTime` datetime DEFAULT NULL, `ProvinceSupervisorConfirmUserID` int DEFAULT NULL, `ProvinceSupervisorConfirmDateTime` datetime DEFAULT NULL, `SupervisorConfirmUserID` int DEFAULT NULL, `SupervisorConfirmDateTime` datetime DEFAULT NULL, `StartDate` datetime DEFAULT CURRENT_TIMESTAMP, `EndDate` datetime DEFAULT NULL, `Weight` decimal(10,1) NOT NULL DEFAULT '1.0', `BudgetUsed` tinyint NOT NULL, `BudgetReserved` tinyint NOT NULL, `RejectedByUserID` int DEFAULT NULL, `RejectedAt` datetime DEFAULT NULL, `RejectedComment` text, PRIMARY KEY (`id`));")
advisers = [u for u in users if u['adv']]
clients = [u for u in users if not u['adv']]
ev_rows = []
eid = 300000
MONTHS = [(2025, 12)] + [(2026, mm) for mm in range(1, 12)]
for (y, mm) in MONTHS:
    n_ev = random.randint(10, 18)
    for k in range(n_ev):
        eid += 1
        cl = random.choice(clients)
        adv = random.choice(advisers)
        ctr = random.choice(CENTERS)
        svc = random.choice(SERVICES)
        is_ems = 1 if svc[0] == 9 else 0
        day = random.randint(1, 28)
        start = f'{y}-{mm:02d}-{day:02d} {random.randint(8,17):02d}:30:00'
        done = random.random() < 0.82
        end = f'{y}-{mm:02d}-{day:02d} {random.randint(18,20):02d}:15:00' if done else None
        # مراحل تایید
        stages = []
        if done:
            nconf = random.choice([3,4,5,5,5])
            c_admin = 3 if nconf >= 1 else None
            c_tech = 7 if nconf >= 2 else None
            c_oper = 15 if nconf >= 3 else None
            c_psup = 16 if nconf >= 4 else None
            c_sup = 17 if nconf >= 5 else None
        else:
            c_admin = c_tech = c_oper = c_psup = c_sup = None
        fee = random.choice([0, 1200000, 1500000, 2000000, 3500000])
        ev_rows.append((eid, cl['id'], cl['nid'], 0, ctr[0], svc[0], 1, 100111400000 + eid,
                        0, 9, 0, is_ems, 1, 6, 0, adv['id'], fee, 0, '', 1, 0, 0, 0,
                        c_admin, f'{y}-{mm:02d}-{day:02d} 19:00:00' if c_admin else None,
                        c_tech, f'{y}-{mm:02d}-{day:02d} 19:10:00' if c_tech else None,
                        c_oper, f'{y}-{mm:02d}-{day:02d} 19:20:00' if c_oper else None,
                        c_psup, f'{y}-{mm:02d}-{day:02d} 19:30:00' if c_psup else None,
                        c_sup, f'{y}-{mm:02d}-{day:02d} 19:40:00' if c_sup else None,
                        start, end, svc[4], 1, 0, None, None, None))
ins('Events', ['id','UserID','NID','TrackingCode','CenterID','ServiceID','ContractID','RefID',
               'EmdadCheck','CorporateContractServiceID','UserTariff','EMS','Level','CenterAdminID',
               'SupervisorID','AcceptorID','AcceptorFee','SecretaryFee','AcceptorCodeName','AcceptorLevel',
               'SupervisorFee','CenterFee','AdminFee','CenterAdminConfirmUserID','CenterAdminConfirmDateTime',
               'CenterTechConfirmUserID','CenterTechConfirmDateTime','OperatorConfirmUserID','OperatorConfirmDateTime',
               'ProvinceSupervisorConfirmUserID','ProvinceSupervisorConfirmDateTime','SupervisorConfirmUserID',
               'SupervisorConfirmDateTime','StartDate','EndDate','Weight','BudgetUsed','BudgetReserved',
               'RejectedByUserID','RejectedAt','RejectedComment'], ev_rows)

add("CREATE TABLE `EventReserves` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int NOT NULL, `UserID` int NOT NULL, `AcceptorID` int NOT NULL, `Date` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('EventReserves', ['id','EventID','UserID','AcceptorID','Date'],
    [(900000+i, ev_rows[i][0], ev_rows[i][1], ev_rows[i][15], ev_rows[i][33]) for i in range(30)])

add("CREATE TABLE `EventsEms` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int NOT NULL, `SecretaryNID` bigint(10) NOT NULL, `EMSType` json DEFAULT NULL, `SuicidalFrom` json DEFAULT NULL, `SuicidalRiskLevel` enum('low','medium','high','norisk') DEFAULT 'norisk', `PsychiatricDisorders` json DEFAULT NULL, `SocialFactors` json DEFAULT NULL, `ProtectiveFactors` json DEFAULT NULL, `SuggestedActions` json DEFAULT NULL, `ActionsTaken` text, `FinancialAssistanceRequest` int NOT NULL DEFAULT '0', `Status` enum('Pending','inProgress','Done','Reject') NOT NULL DEFAULT 'Pending', `DateTime` datetime NOT NULL, `HadPaymentAmount` bigint DEFAULT NULL, `HadPaymentStatus` varchar(20) DEFAULT NULL, `HadPaymentDescription` text, `ConfirmedByUserID` int DEFAULT NULL, PRIMARY KEY (`id`));")
ems_rows = []
ems_id = 500
for i, r in enumerate(ev_rows):
    if r[11] == 1:
        ems_id += 1
        st = random.choice(['Pending','inProgress','Done','Done','Reject'])
        risk = random.choice(['low','medium','high'])
        amt = random.choice([3000000, 5000000, None])
        ems_rows.append((ems_id, r[0], 3540083960, '["selfharm"]', '["family"]', risk, '["depression"]',
                         '["unemployment"]', '["family support"]', '["hospitalize"]', 'بستری و پیگیری',
                         1 if amt else 0, st, r[33], amt,
                         'پرداخت شده' if (st == 'Done' and amt) else ('در انتظار پرداخت' if amt else None),
                         'کمکی به خانواده' if amt else None, 17 if st == 'Done' else None))
ins('EventsEms', ['id','EventID','SecretaryNID','EMSType','SuicidalFrom','SuicidalRiskLevel','PsychiatricDisorders',
                  'SocialFactors','ProtectiveFactors','SuggestedActions','ActionsTaken','FinancialAssistanceRequest',
                  'Status','DateTime','HadPaymentAmount','HadPaymentStatus','HadPaymentDescription','ConfirmedByUserID'],
    ems_rows or [(500, ev_rows[0][0], 3540083960, None, None, 'low', None, None, None, None, None, 0, 'Pending', '2026-01-05 10:00:00', None, None, None, None)])

add("CREATE TABLE `EventEmsComments` (`id` int NOT NULL AUTO_INCREMENT, `EventEmsID` int NOT NULL, `UserID` int DEFAULT NULL, `Comment` varchar(255) NOT NULL, `Date` datetime NOT NULL, PRIMARY KEY (`id`));")
if ems_rows:
    ins('EventEmsComments', ['id','EventEmsID','UserID','Comment','Date'],
        [(700+i, ems_rows[i][0], None, 'طبق کمیسیون برگزار شده با حضور مشاور و روانپزشک', '2026-05-12 07:50:50')
         for i in range(min(3, len(ems_rows)))])

# ---------------- ارجاع‌ها ----------------
add("CREATE TABLE `Referrs` (`id` int NOT NULL AUTO_INCREMENT, `RefID` bigint NOT NULL, `UserID` int NOT NULL, `ServiceID` int NOT NULL DEFAULT '0', `Description` text, `Status` enum('Pending','inProgress','Done') NOT NULL DEFAULT 'Pending', `IsReferr` bit(1) NOT NULL DEFAULT b'0', `ProvinceID` int NOT NULL DEFAULT '0', `CityID` int NOT NULL DEFAULT '0', `CenterID` int DEFAULT NULL, `AcceptorID` int DEFAULT NULL, `AdminReferrerID` int DEFAULT NULL, `CreationDate` datetime NOT NULL, `Type` enum('soha','inPerson') NOT NULL DEFAULT 'soha', PRIMARY KEY (`id`));")
ref_rows = []
rid = 900
for i in range(40):
    rid += 1
    cl = random.choice(clients)
    prov = random.choice(PROV)
    st = random.choice(['Pending','inProgress','Done','Done'])
    ref_rows.append((rid, 100110000000 + rid, cl['id'], 5, 'درخواست مشاوره دارند', st, 1,
                     prov[0], random.choice([c for c in CITIES if c[1] == prov[0]] or CITIES)[0],
                     random.choice([None, 22, 28]), random.choice([None] + [a['id'] for a in advisers]),
                     None, f'2026-{random.randint(1,11):02d}-{random.randint(1,28):02d} 10:00:00', 'soha'))
ins('Referrs', ['id','RefID','UserID','ServiceID','Description','Status','IsReferr','ProvinceID','CityID','CenterID','AcceptorID','AdminReferrerID','CreationDate','Type'], ref_rows)

add("CREATE TABLE `ReferrsRequest` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `Description` mediumtext, `Status` enum('Pending','inProgress','Done') NOT NULL DEFAULT 'Pending', `ProvinceID` int NOT NULL DEFAULT '0', `CityID` int NOT NULL DEFAULT '0', `CenterID` int DEFAULT NULL, `AdminReferrerID` int DEFAULT NULL, `CreationDate` datetime NOT NULL, `EditionDate` datetime DEFAULT NULL, PRIMARY KEY (`id`));")
ins('ReferrsRequest', ['id','UserID','Description','Status','ProvinceID','CityID','CenterID','AdminReferrerID','CreationDate','EditionDate'],
    [(800+i, random.choice(clients)['id'], None, random.choice(['Pending','inProgress','Done']),
      8, 301, 22, None, f'2026-{random.randint(1,11):02d}-{random.randint(1,28):02d} 12:00:00', None) for i in range(15)])

add("CREATE TABLE `ReferrFollowUps` (`id` int NOT NULL AUTO_INCREMENT, `ReferrID` int NOT NULL, `UserID` int NOT NULL, `Comment` text NOT NULL, `CreatedAt` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('ReferrFollowUps', ['id','ReferrID','UserID','Comment','CreatedAt'],
    [(600+i, ref_rows[i][0], 7, 'عدم همکاری (خاموش)', '2026-08-08 10:21:14') for i in range(5)])

# ---------------- گروه‌ها ----------------
add("CREATE TABLE `Groups` (`id` int NOT NULL AUTO_INCREMENT, `Type` enum('counseling','educational') NOT NULL, `CorporateContractID` int DEFAULT NULL, `CenterID` int NOT NULL, `AcceptorID` int NOT NULL, `CreatorID` int DEFAULT NULL, `Tel` varchar(15) DEFAULT NULL, `Address` varchar(255) NOT NULL, `Status` enum('pending','confirmed','rejected','draft') NOT NULL, `CreateDate` datetime NOT NULL, PRIMARY KEY (`id`));")
groups = []
for gi in range(1, 7):
    groups.append((gi, 'counseling', 51, random.choice(CENTERS)[0], random.choice(advisers)['id'],
                   7, '02112345678', 'آدرس گروه', 'confirmed', f'2026-0{random.randint(1,9)}-15 10:00:00'))
ins('Groups', ['id','Type','CorporateContractID','CenterID','AcceptorID','CreatorID','Tel','Address','Status','CreateDate'], groups)

add("CREATE TABLE `GroupEvents` (`id` int NOT NULL AUTO_INCREMENT, `GroupID` int NOT NULL, `Topic` varchar(255) NOT NULL, `Description` varchar(255) DEFAULT NULL, `StartDate` datetime DEFAULT NULL, `EndDate` datetime DEFAULT NULL, `SessionNumber` int DEFAULT NULL, `AcceptorID` int DEFAULT NULL, `AcceptorCodeName` varchar(100) DEFAULT NULL, `AcceptorLevel` tinyint DEFAULT '1', `SupervisorID` int DEFAULT NULL, `CenterAdminID` int DEFAULT NULL, `AcceptorFee` int DEFAULT '0', `SecretaryFee` int NOT NULL DEFAULT '0', `ServiceID` int DEFAULT NULL, `ContractID` int DEFAULT NULL, `UserTariff` int DEFAULT NULL, `BudgetReserved` tinyint NOT NULL DEFAULT '0', `BudgetUsed` tinyint NOT NULL DEFAULT '0', `Weight` decimal(10,1) NOT NULL DEFAULT '1.0', `CenterID` int DEFAULT NULL, `OperatorConfirmUserID` int DEFAULT NULL, `OperatorConfirmDateTime` datetime DEFAULT NULL, `SupervisorConfirmUserID` int DEFAULT NULL, `SupervisorConfirmDateTime` datetime DEFAULT NULL, PRIMARY KEY (`id`));")
ge_rows = []
ge_id = 1400
for gi in range(1, 7):
    for sess in range(1, 5):
        ge_id += 1
        y, mm = (2026, random.randint(1, 11))
        done = random.random() < 0.8
        start = f'{y}-{mm:02d}-{random.randint(1,28):02d} 10:00:00'
        ge_rows.append((ge_id, gi, 'جلسه مشاوره گروهی', None, start,
                        start if done else None, sess, groups[gi-1][4], 'adviser', 1, None, None,
                        5180000, 0, 6, 51, 0, 0, 1 if done else 0, 1.0, groups[gi-1][3],
                        15 if done else None, start if done else None, 17 if done else None, start if done else None))
ins('GroupEvents', ['id','GroupID','Topic','Description','StartDate','EndDate','SessionNumber','AcceptorID',
                    'AcceptorCodeName','AcceptorLevel','SupervisorID','CenterAdminID','AcceptorFee','SecretaryFee',
                    'ServiceID','ContractID','UserTariff','BudgetReserved','BudgetUsed','Weight','CenterID',
                    'OperatorConfirmUserID','OperatorConfirmDateTime','SupervisorConfirmUserID','SupervisorConfirmDateTime'], ge_rows)

add("CREATE TABLE `GroupMembers` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `NID` bigint(10) NOT NULL, `GroupID` int NOT NULL, `RefID` bigint DEFAULT NULL, `DateTime` datetime NOT NULL, PRIMARY KEY (`id`));")
gm_rows = []
gm_id = 30
for gi in range(1, 7):
    for k in range(6):
        gm_id += 1
        cl = random.choice(clients)
        gm_rows.append((gm_id, cl['id'], cl['nid'], gi, None, '2026-01-13 08:09:14'))
ins('GroupMembers', ['id','UserID','NID','GroupID','RefID','DateTime'], gm_rows)

add("CREATE TABLE `GroupEventMember` (`id` bigint NOT NULL AUTO_INCREMENT, `UserID` bigint NOT NULL, `GroupID` bigint NOT NULL, `GroupEventID` bigint DEFAULT NULL, `ServiceID` int DEFAULT NULL, `TrackingCode` int DEFAULT '0', `RefID` bigint DEFAULT NULL, `DateTime` datetime NOT NULL, PRIMARY KEY (`id`));")
gem_rows = []
gem_id = 11000
for ge in ge_rows:
    if ge[5]:  # انجام‌شده
        for k in range(random.randint(3, 6)):
            gem_id += 1
            cl = random.choice(clients)
            gem_rows.append((gem_id, cl['id'], ge[1], ge[0], 6, 0, None, ge[4]))
ins('GroupEventMember', ['id','UserID','GroupID','GroupEventID','ServiceID','TrackingCode','RefID','DateTime'], gem_rows)

# ---------------- بودجه ----------------
add("CREATE TABLE `Budget` (`Id` int NOT NULL AUTO_INCREMENT, `Title` varchar(255) DEFAULT NULL, `Type` enum('Main','Group','Job') DEFAULT NULL, `Amount` decimal(10,1) NOT NULL DEFAULT '0.0', `Remained` decimal(10,1) NOT NULL DEFAULT '0.0', `Reserved` decimal(10,1) NOT NULL DEFAULT '0.0', `StartDate` datetime DEFAULT NULL, `EndDate` datetime DEFAULT NULL, `CreateTime` datetime DEFAULT NULL, `AmountBefore` decimal(10,1) NOT NULL, `Used` decimal(10,1) NOT NULL, `Assigned` decimal(10,1) NOT NULL, PRIMARY KEY (`Id`));")
ins('Budget', ['Id','Title','Type','Amount','Remained','Reserved','StartDate','EndDate','CreateTime','AmountBefore','Used','Assigned'],
    [(8,'سهمیه خدمات گروهی','Group',9701.0,5752.0,1427.0,'2025-12-22 00:00:00','2026-07-22 23:59:00','2026-01-18 15:01:30',299.0,2682.0,9788.0),
     (9,'سهمیه مشاوره شغلی (بنیاد حیات)','Job',5000.0,4989.0,10.0,'2025-12-22 00:00:00','2027-02-20 23:59:00','2026-04-21 15:03:33',0.0,2.0,5000.0),
     (10,'سهمیه خدمات فردی','Main',5000.0,4200.0,120.0,'2025-12-22 00:00:00','2026-12-22 23:59:00','2026-05-01 09:00:00',0.0,700.0,5000.0)])
add("CREATE TABLE `BudgetProvince` (`Id` int NOT NULL AUTO_INCREMENT, `BudgetId` int DEFAULT NULL, `ProvinceId` int DEFAULT NULL, `Amount` decimal(10,1) NOT NULL DEFAULT '0.0', `Remained` decimal(10,1) NOT NULL DEFAULT '0.0', `Reserved` decimal(10,1) NOT NULL DEFAULT '0.0', `CreateTime` datetime DEFAULT NULL, `AmountBefore` decimal(10,1) NOT NULL, `Used` decimal(10,1) NOT NULL, `Assigned` decimal(10,1) NOT NULL, PRIMARY KEY (`Id`));")
ins('BudgetProvince', ['Id','BudgetId','ProvinceId','Amount','Remained','Reserved','CreateTime','AmountBefore','Used','Assigned'],
    [(12,8,1,326.0,198.0,14.0,'2026-01-18 15:08:40',0.0,114.0,0.0),
     (13,8,4,174.0,70.0,48.0,'2026-01-18 15:08:40',0.0,56.0,0.0),
     (14,8,8,900.0,540.0,60.0,'2026-01-18 15:08:40',0.0,300.0,0.0)])

# ---------------- مالی/پیامک/لاگ ----------------
add("CREATE TABLE `Incomes` (`id` int NOT NULL AUTO_INCREMENT, `CenterID` int DEFAULT NULL, `UserID` int DEFAULT NULL, `EventID` int DEFAULT NULL, `Type` varchar(50) DEFAULT NULL, `Title` varchar(255) DEFAULT NULL, `Fee` int DEFAULT NULL, `IncomeDate` datetime DEFAULT NULL, `DateTime` datetime DEFAULT NULL, `Description` text, `FileID` varchar(11) NOT NULL, PRIMARY KEY (`id`));")
ins('Incomes', ['id','CenterID','UserID','Type','Title','Fee','IncomeDate','DateTime','FileID'],
    [(100+i, 22, 7, 'خدمات', 'درآمد خدمات ' + str(i), random.randint(500000, 5000000),
      f'2026-{random.randint(1,11):02d}-15 10:00:00', None, '') for i in range(12)])
add("CREATE TABLE `Expenses` (`id` int NOT NULL AUTO_INCREMENT, `CenterID` int DEFAULT NULL, `UserID` int DEFAULT NULL, `Category` varchar(50) DEFAULT NULL, `Type` varchar(100) DEFAULT NULL, `Title` varchar(255) NOT NULL, `PayTo` varchar(100) DEFAULT NULL, `PayType` varchar(50) DEFAULT NULL, `Fee` int DEFAULT NULL, `PayDate` datetime DEFAULT NULL, `DateTime` datetime DEFAULT NULL, `Description` text, `FileID` varchar(11) NOT NULL, PRIMARY KEY (`id`));")
ins('Expenses', ['id','CenterID','UserID','Category','Type','Title','PayTo','PayType','Fee','PayDate','DateTime','FileID'],
    [(200+i, 22, 7, 'اجاره', 'ماهانه', 'اجاره محل ' + str(i), 'مالک', 'کارت به کارت',
      random.randint(2000000, 9000000), f'2026-{random.randint(1,11):02d}-01 10:00:00', None, '') for i in range(10)])

add("CREATE TABLE `SMS` (`id` int NOT NULL AUTO_INCREMENT, `SmsSender` int NOT NULL, `SmsReceiver` int NOT NULL, `Number` bigint(11) NOT NULL, `Message` varchar(255) NOT NULL DEFAULT '', `Response` text, `Status` enum('Pending','Failed','Success') NOT NULL DEFAULT 'Pending', `Efforts` int NOT NULL DEFAULT '0', `UpdateTime` datetime NOT NULL, `CreateTime` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('SMS', ['id','SmsSender','SmsReceiver','Number','Message','Response','Status','Efforts','UpdateTime','CreateTime'],
    [(2+i, 7, random.choice(clients)['id'], random.randint(9100000000, 9999999999),
      'مورد حاد\nنام و نام خانوادگی: تست', '', random.choice(['Success','Success','Success','Failed']),
      1, '2025-01-08 12:55:52', f'2025-{random.randint(1,12):02d}-14 10:35:56') for i in range(25)])

add("CREATE TABLE `Log` (`id` int NOT NULL AUTO_INCREMENT, `uid` int NOT NULL, `Category` varchar(255) DEFAULT NULL, `Description` text, `Level` tinyint NOT NULL DEFAULT '0', `IP` varchar(255) NOT NULL DEFAULT 'UNKNOWN', `Timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`));")
LOGCATS = ['LOGIN','SECRETARY','API','EMS','CONFIRM']
ins('Log', ['id','uid','Category','Description','Level','IP','Timestamp'],
    [(1382771+i, random.choice(users)['id'], random.choice(LOGCATS),
      random.choice(['کاربر وارد سیستم شد.', 'جلسه بعدی برای کاربر رزرو شد در تاریخ: 1404/10/20',
                     'جلسه تایید شد توسط مسئول مربوطه', 'فراخوانی API سها موفق']),
      5, '192.168.69.66', f'2026-{random.randint(1,11):02d}-{random.randint(1,28):02d} 05:19:53') for i in range(60)])

add("CREATE TABLE `Messages` (`id` int NOT NULL AUTO_INCREMENT, `FromUID` int NOT NULL, `ToUID` int DEFAULT NULL, `Subject` varchar(255) DEFAULT NULL, `Text` text, `FileID` int DEFAULT NULL, `TargetRole` varchar(50) DEFAULT NULL, `TargetProvinceID` int DEFAULT NULL, `Timestamp` datetime NOT NULL, `Star` tinyint(1) NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
ins('Messages', ['id','FromUID','ToUID','Subject','Text','TargetRole','TargetProvinceID','Timestamp','Star'],
    [(2, 7, 251838, 'سلام', 'تست ارسال پیام', None, None, '2026-02-10 09:22:38', 0),
     (6, 7, None, 'اطلاعیه سراسری', 'جلسه هماهنگی روز شنبه برگزار می‌شود', 'adviser', 8, '2026-03-01 08:00:00', 1)])

add("CREATE TABLE `Sessions` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `Key` varchar(255) DEFAULT NULL, `IP` varchar(20) DEFAULT NULL, `Browser` varchar(255) DEFAULT NULL, `DateTime` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('Sessions', ['id','UserID','Key','IP','Browser','DateTime'],
    [(1060681+i, random.choice(users)['id'], '5f8aa4e3d58d7fa8d6f8328504630dc8d1f875', '192.168.1.2',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', f'2026-09-1{random.randint(0,1)} 05:08:53') for i in range(10)])

# ---------------- مشاوران ----------------
add("CREATE TABLE `ConsultantTax` (`id` int NOT NULL AUTO_INCREMENT, `NID` bigint(10) NOT NULL, `Year` smallint NOT NULL, `Month` tinyint NOT NULL, `TaxAmount` bigint NOT NULL DEFAULT '0', `ExemptionMonths` tinyint NOT NULL DEFAULT '1', `MultiEmployerMonth` tinyint NOT NULL DEFAULT '0', `MultiEmployerYear` tinyint NOT NULL DEFAULT '0', `TotalPayment` bigint NOT NULL DEFAULT '0', `CreatedByUserID` int DEFAULT NULL, `CreatedAt` datetime NOT NULL, PRIMARY KEY (`id`));")
tax_rows = []
tid = 1
for a in advisers[:6]:
    for month in range(1, 10):
        tid += 1
        total = random.randint(20000000, 90000000)
        tax_rows.append((tid, a['nid'], 1405, month, int(total * 0.1), random.randint(1,4), 0, 0, total, 236452, f'2026-07-28 15:15:08'))
ins('ConsultantTax', ['id','NID','Year','Month','TaxAmount','ExemptionMonths','MultiEmployerMonth','MultiEmployerYear','TotalPayment','CreatedByUserID','CreatedAt'], tax_rows)

add("CREATE TABLE `ConsultantEducation` (`id` int NOT NULL AUTO_INCREMENT, `UserID` int NOT NULL, `ConsultantNID` bigint(10) DEFAULT NULL, `Field` varchar(255) DEFAULT NULL, `Orientation` varchar(255) DEFAULT NULL, `Grade` varchar(255) DEFAULT NULL, `Univesity` varchar(255) DEFAULT NULL, `GraduationDate` varchar(25) DEFAULT NULL, `DateTime` datetime DEFAULT CURRENT_TIMESTAMP, `File` varchar(255) DEFAULT NULL, PRIMARY KEY (`id`));")
ins('ConsultantEducation', ['id','UserID','ConsultantNID','Field','Orientation','Grade','Univesity','GraduationDate','DateTime','File'],
    [(5699+i, a['id'], a['nid'], 'روانشناسی', 'بالینی', str(random.randint(6,9)), 'دانشگاه آزاد', str(1400+i), '2026-03-16 04:36:52', None)
     for i, a in enumerate(advisers[:8])])

add("CREATE TABLE `InvitePersons` (`ID` int NOT NULL AUTO_INCREMENT, `NID` bigint(10) DEFAULT NULL, `Name` varchar(60) NOT NULL, `Mobile` varchar(12) NOT NULL, `Phone` varchar(12) DEFAULT NULL, `Description` varchar(255) DEFAULT NULL, `Response` varchar(255) DEFAULT NULL, `Status` enum('ارجاع شده','در حال بررسی','اتمام بررسی') NOT NULL, `GroupID` varchar(11) DEFAULT NULL, `GroupName` varchar(255) DEFAULT NULL, `ProvinceID` int DEFAULT NULL, `CityID` int DEFAULT NULL, `CenterID` int DEFAULT NULL, `CreateTime` datetime NOT NULL, `UpdateTime` datetime DEFAULT NULL, PRIMARY KEY (`ID`));")
ins('InvitePersons', ['ID','NID','Name','Mobile','Phone','Description','Response','Status','GroupID','GroupName','ProvinceID','CityID','CenterID','CreateTime','UpdateTime'],
    [(i+1, random.randint(1000000000, 9999999999), random.choice(FIRST) + ' ' + random.choice(FAM),
      str(random.randint(9100000000, 9999999999)), None, 'کارجو', 'ارجاع دادیم به مشاور',
      random.choice(['ارجاع شده','در حال بررسی','اتمام بررسی']), '279267', 'حیاط', 8, 301, 443,
      '2025-12-16 10:52:22', '2026-10-11 14:53:44') for i in range(12)])

add("CREATE TABLE `CareerCounseling` (`id` int NOT NULL AUTO_INCREMENT, `RequestStatus` varchar(20) DEFAULT 'در جریان', `ProvinceID` int DEFAULT NULL, `Province` varchar(50) DEFAULT NULL, `Office` varchar(100) DEFAULT NULL, `ApplicantNID` bigint(10) DEFAULT NULL, `ApplicantName` varchar(150) DEFAULT NULL, `ApplicantMobile` bigint(11) DEFAULT NULL, `ApplicantGender` varchar(20) DEFAULT NULL, `TargetGroup` varchar(50) DEFAULT NULL, `ApplicationDate` datetime DEFAULT NULL, `InstituteProvinceID` int DEFAULT NULL, `InstituteProvince` varchar(50) DEFAULT NULL, `Institute` varchar(100) DEFAULT NULL, `ConsultantID` int DEFAULT NULL, `Status` enum('مشاهده نشده','در حال انجام','ثبت شده') DEFAULT 'مشاهده نشده', `CreateDate` datetime DEFAULT NULL, `AgentID` int DEFAULT NULL, `BudgetReserved` tinyint NOT NULL DEFAULT '0', `BudgetUsed` tinyint NOT NULL DEFAULT '0', `Weight` decimal(10,1) NOT NULL DEFAULT '1.0', PRIMARY KEY (`id`));")
ins('CareerCounseling', ['id','RequestStatus','ProvinceID','Province','Office','ApplicantNID','ApplicantName','ApplicantMobile','ApplicantGender','TargetGroup','ApplicationDate','InstituteProvinceID','InstituteProvince','Institute','ConsultantID','Status','CreateDate','AgentID','BudgetReserved','BudgetUsed','Weight'],
    [(i+1, 'درجریان', 30, 'همدان', 'اداره همدان', random.randint(1000000000, 9999999999),
      random.choice(FIRST) + ' ' + random.choice(FAM), random.randint(9100000000, 9999999999), 'زن',
      'نگهداری کودک، سالمند', f'2026-0{random.randint(4,9)}-20 00:00:00', 8, 'تهران',
      'راه زندگی رز سفید-حقوقی', None, random.choice(['مشاهده نشده','در حال انجام','ثبت شده']),
      '2026-04-20 00:00:00', None, 0, 0, 1.0) for i in range(10)])

add("CREATE TABLE `CorporateContracts` (`id` int NOT NULL AUTO_INCREMENT, `CorporateCustomerID` int NOT NULL, `AppDefault` tinyint NOT NULL DEFAULT '0', `StartDate` datetime NOT NULL, `EndDate` datetime NOT NULL, `Detect` enum('Always','API','NID','Coupon') NOT NULL DEFAULT 'NID', `Remove` tinyint(1) NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
add("CREATE TABLE `CorporateCustomers` (`id` int NOT NULL AUTO_INCREMENT, `Title` varchar(255) DEFAULT NULL, `Discount` int DEFAULT NULL, `Phone` varchar(50) DEFAULT NULL, PRIMARY KEY (`id`));")
ins('CorporateCustomers', ['id','Title','Discount','Phone'], [(1,'شرکت آزمایشی',0,'02188887777'),(2,'بنیاد حیات',0,'02155554444')])
ins('CorporateContracts', ['id','CorporateCustomerID','AppDefault','StartDate','EndDate','Detect','Remove'],
    [(1,1,1,'2024-08-28 15:27:32','2026-12-31 15:27:35','Always',0),(2,2,1,'2025-08-28 15:27:58','2026-12-31 15:28:01','NID',0)])
add("CREATE TABLE `CorporateContractServices` (`id` int NOT NULL AUTO_INCREMENT, `CorporateContractID` int NOT NULL, `ServiceID` int NOT NULL, `UserTariff` int NOT NULL, `ConsultantLevel1` int NOT NULL DEFAULT '0', `ConsultantLevel2` int NOT NULL DEFAULT '0', `ConsultantLevel3` int NOT NULL DEFAULT '0', `ConsultantLevel4` int NOT NULL DEFAULT '0', `ConsultantLevel5` int NOT NULL DEFAULT '0', `ConsultantDR` int NOT NULL DEFAULT '0', `SecretaryFee` int NOT NULL DEFAULT '0', `SupervisorFee` int NOT NULL DEFAULT '0', `CenterFee` int NOT NULL DEFAULT '0', `AdminFee` int NOT NULL DEFAULT '0', PRIMARY KEY (`id`));")
ins('CorporateContractServices', ['id','CorporateContractID','ServiceID','UserTariff','ConsultantLevel1','ConsultantLevel2','ConsultantLevel3','ConsultantLevel4','ConsultantLevel5','ConsultantDR','SecretaryFee','SupervisorFee','CenterFee','AdminFee'],
    [(9, 2, 1, 0, 1200000, 1500000, 2000000, 2500000, 3000000, 4000000, 100000, 200000, 300000, 200000),
     (10, 2, 6, 0, 5000000, 5180000, 5400000, 0, 0, 0, 0, 0, 0, 0)])

# ---------------- بالینی ----------------
add("CREATE TABLE `EventPsychology` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int DEFAULT NULL, `UserID` int DEFAULT NULL, `AcceptorID` int DEFAULT NULL, `Job` varchar(255) DEFAULT NULL, `Ethnicity` varchar(255) DEFAULT NULL, `Religion` varchar(255) DEFAULT NULL, `ReligiousBelief` varchar(255) DEFAULT NULL, `Children` int DEFAULT NULL, `ResidenceQuality` text, `SpouseInfo` text, `ProblemStart` text, `ProblemDuration` text, `ClinicalObservation` text, `Appearance` text, `PsychomotorStatus` text, `InterviewAttitude` text, `Mood` text, `Affect` text, `Speech` text, `Perception` text, `ThoughtContent` text, `ThoughtProcess` text, `Consciousness` text, `Orientation` text, `Memory` text, `Concentration` text, `Intelligence` text, `Judgment` text, `Insight` text, `MedicalHistory` text, `FamilyHistory` text, `FamilyRelationships` text, `DateTime` datetime DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`));")
ins('EventPsychology', ['id','EventID','UserID','AcceptorID','Job','Ethnicity','Religion','ReligiousBelief','Children','ResidenceQuality','SpouseInfo','ProblemStart','ProblemDuration','ClinicalObservation','Appearance','PsychomotorStatus','InterviewAttitude','Mood','Affect','Speech','Perception','ThoughtContent','ThoughtProcess','Consciousness','Orientation','Memory','Concentration','Intelligence','Judgment','Insight','MedicalHistory','FamilyHistory','FamilyRelationships','DateTime'],
    [(23, ev_rows[0][0], ev_rows[0][1], ev_rows[0][15], 'خانه دار', 'فارس', 'اسلام شیعه', 'متوسط', 3,
      'در منزل وراث زندگی مینماید', '۷ ساله فوت نموده', 'میانسالی', 'بیشتر از ۴ سال',
      'خشم و بی حوصلگی غم و گریه کردن مکرر', 'خمودگی', 'کندی حرکتی روانی', 'علاقمند', 'افسرده',
      'کند', 'متناسب', 'نرمال', '', 'در حال بررسی', 'نرمال', 'نرمال', 'درگیری افکار', 'کم',
      'در حد معمول', 'نرمال', 'دارد', 'چیزی گزارش نشده', 'خواهر در اثر تصادف فوت نموده', 'نزدیک',
      '2026-03-16 07:48:01'),
     (24, ev_rows[1][0], ev_rows[1][1], ev_rows[1][15], 'دانش آموز', 'فارس', 'اسلام شیعه', 'زیاد', 0,
      'خوب است', 'ندارد', 'نوجوانی', 'زیر ۶ ماه', 'شناختی روانی هیجانی', 'تحرک داشته',
      'عصبانی بوده است', 'همکاری داشته', 'حراسان هست', 'محدود هست', 'خوب', 'خوب', 'افکار پرش',
      'در حال بررسی', 'سالم', 'خوب', 'خوب', 'دارد', 'خوب', 'نرمال', 'دارد', 'خیر', 'خوب', 'خوب',
      '2026-03-16 09:37:54')])

add("CREATE TABLE `EventComments` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int NOT NULL, `ConsultantNID` bigint(10) NOT NULL, `Comment` text, `DateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`));")
ins('EventComments', ['id','EventID','ConsultantNID','Comment','DateTime'],
    [(5, ev_rows[0][0], 158795, 'تست یادداشت — جلسه اول', '2024-12-09 08:17:03'),
     (6, ev_rows[1][0], 158795, 'پیگیری جلسه دوم', '2024-12-09 08:39:58')])

add("CREATE TABLE `EventNeuroFeedback` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int NOT NULL, `Protocol` varchar(255) DEFAULT NULL, `Target` varchar(255) DEFAULT NULL, `Visible` varchar(255) DEFAULT NULL, `Action` varchar(255) DEFAULT NULL, `Changed` varchar(255) DEFAULT NULL, `EzterabOld` tinyint DEFAULT NULL, `EzterabNew` tinyint DEFAULT NULL, `AfsorOld` tinyint DEFAULT NULL, `AfsorNew` tinyint DEFAULT NULL, `SleepProblemOld` tinyint DEFAULT NULL, `SleepProblemNew` tinyint DEFAULT NULL, `FocusOld` tinyint DEFAULT NULL, `FocusNew` tinyint DEFAULT NULL, `EnergyOld` tinyint DEFAULT NULL, `EnergyNew` tinyint DEFAULT NULL, `Other` varchar(255) DEFAULT NULL, `DateTime` datetime DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`));")
nf_events = [r for r in ev_rows if r[5] == 11][:2]
if nf_events:
    ins('EventNeuroFeedback', ['id','EventID','Protocol','Target','Visible','Action','Changed','EzterabOld','EzterabNew','AfsorOld','AfsorNew','SleepProblemOld','SleepProblemNew','FocusOld','FocusNew','EnergyOld','EnergyNew','Other','DateTime'],
        [(292511+i, r[0], 'f', 'افسردگی', 'آرامش بیشتر بعد از جلسات', 'رغبت بیشتر برای شرکت در جلسه',
          'بهبود خلق', random.randint(0,9), random.randint(0,9), random.randint(0,9), random.randint(0,9),
          0, 0, 0, 0, 0, 0, 'تغییرات واضح در عاطفه', '2026-03-16 11:04:17') for i, r in enumerate(nf_events)])

add("CREATE TABLE `EventHeadMap` (`id` int NOT NULL AUTO_INCREMENT, `EventID` int NOT NULL, `FileID` varchar(255) DEFAULT NULL, `Description` varchar(255) DEFAULT NULL, `DateTime` datetime DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`));")
hm_events = [r for r in ev_rows if r[5] == 12][:2]
if hm_events:
    ins('EventHeadMap', ['id','EventID','FileID','Description','DateTime'],
        [(292511+i, r[0], '1', 'توجه و تمرکز پائین، امواج بتا بسیار بالا', '2026-03-17 13:29:50')
         for i, r in enumerate(hm_events)])

add("CREATE TABLE `Files` (`id` int NOT NULL AUTO_INCREMENT, `UserNID` bigint(10) NOT NULL, `Name` varchar(255) NOT NULL, `Location` varchar(1024) NOT NULL, `UploadDateTime` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('Files', ['id','UserNID','Name','Location','UploadDateTime'],
    [(1, users[0]['nid'], 'head-map-file-1', '/userfiles/eventfiles/2026/03/69b95793', '2026-03-17 17:00:17'),
     (2, users[1]['nid'], 'consultant-resume', '/userfiles/resume/2026/03/69b98ad0c9c8', '2026-03-17 20:39:17')])

add("CREATE TABLE `SpecialOccasions` (`id` int NOT NULL AUTO_INCREMENT, `Title` varchar(255) NOT NULL, `ImagePath` varchar(512) NOT NULL, `DisplayDate` date NOT NULL, `IsActive` tinyint(1) NOT NULL DEFAULT '1', `CreatedByUserID` int DEFAULT NULL, `CreatedAt` datetime NOT NULL, PRIMARY KEY (`id`));")
ins('SpecialOccasions', ['id','Title','ImagePath','DisplayDate','IsActive','CreatedByUserID','CreatedAt'],
    [(1, 'هفته سلامت روان بر تمامی همکاران فرخنده باد', '/uploads/occasions/o1', '2026-10-11', 1, 7, '2026-10-10 11:56:46')])
add("CREATE TABLE `Settings` (`Name` varchar(255) NOT NULL, `Value` varchar(255) DEFAULT NULL, PRIMARY KEY (`Name`));")
ins('Settings', ['Name','Value'], [('BudgetCheckGroup','false'),('BudgetCheckIndividual','false'),('SiteTitle','راه زندگی')])
add("CREATE TABLE `ApiReports` (`id` int NOT NULL AUTO_INCREMENT, `Type` varchar(255) NOT NULL, `Data` json NOT NULL, `Status` enum('Pending','Failed','Success','Error') NOT NULL DEFAULT 'Pending', `Response` tinytext, `Efforts` tinyint DEFAULT '0', `CreateTime` datetime NOT NULL, `UpdateTime` datetime DEFAULT NULL, PRIMARY KEY (`id`));")
ins('ApiReports', ['id','Type','Data','Status','Response','Efforts','CreateTime','UpdateTime'],
    [(5,'UserReport','{"modat": 60, "natije": "تست۱۱"}','Success','OK',1,'2025-01-22 10:04:10','2025-01-22 10:04:11'),
     (6,'UserReport','{"modat": 45, "natije": "تست تست"}','Success','OK',1,'2025-01-25 06:45:38','2025-01-25 06:45:39')])
add("CREATE TABLE `Helps` (`id` int NOT NULL AUTO_INCREMENT, `RoleID` int NOT NULL, `File_1` varchar(255) NOT NULL, PRIMARY KEY (`id`));")
ins('Helps', ['id','RoleID','File_1'], [(1,8,'/uploads/help/adviser.pdf'),(2,6,'/uploads/help/center-admin.pdf')])

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('-- sample backup for testing\n')
    f.write('\n'.join(L))
print(f'OK -> {OUT} ({len(L)} statements)')

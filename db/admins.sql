PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE departments (
    department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    version INTEGER DEFAULT 0,
    date_created TEXT
);
INSERT INTO departments VALUES(2,'Суппорт',0,1,'2026-07-27T16:02:50.257132');
INSERT INTO departments VALUES(3,'1С',1,0,'2026-07-27T16:03:05.569976');
INSERT INTO departments VALUES(4,'прочее',0,0,'2026-07-27T16:03:18.429471');
INSERT INTO departments VALUES(5,'web',1,0,'2026-09-07T17:04:25.825200');
INSERT INTO departments VALUES(6,'string',1,0,'2026-09-17T15:35:34.192095');
INSERT INTO departments VALUES(7,'string11',1,4,'2026-09-17T15:35:51.759106');
CREATE TABLE employees (
	employee_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	first_name TEXT,
	last_name TEXT,
	email TEXT,
	phone TEXT,
	date_created TEXT,
	address TEXT,
	enabled INTEGER DEFAULT (1),
	version INTEGER DEFAULT 0,
	is_admin INTEGER);
INSERT INTO employees VALUES(122,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19T13:29:27',NULL,1,4,1);
INSERT INTO employees VALUES(181,'Тэга','','','','2026-09-08T14:11:07+00:00',NULL,1,2,1);
INSERT INTO employees VALUES(182,'Иван','Иванов','','','2026-09-08 14:16:39.273241+00:00',NULL,0,3,0);
INSERT INTO employees VALUES(183,'Петрй','Петров','','','2026-09-08 14:17:00.090027+00:00',NULL,0,3,0);
INSERT INTO employees VALUES(184,'Роман','Новичихин','','','2026-09-09 12:45:17.526999+00:00',NULL,1,4,0);
INSERT INTO employees VALUES(185,'Директор','','','','2026-09-09 12:46:11.393423+00:00',NULL,1,0,0);
INSERT INTO employees VALUES(186,'Новый admin','last name','email@dfwfw.ru','','2026-09-09T18:15:07',NULL,1,1,1);
INSERT INTO employees VALUES(187,'Новый admin','last name','email@dfwfw.ru','','2026-09-10T14:28:51',NULL,1,1,1);
INSERT INTO employees VALUES(188,'Новый admin1','last name','email@dfwfw.ru','','2026-09-10T14:29:12',NULL,1,1,1);
INSERT INTO employees VALUES(189,'Новый admin1','last name','email@dfwfw.ru','','2026-09-10T14:29:20',NULL,1,1,1);
INSERT INTO employees VALUES(190,'Новый admin1','last name','email@dfwfw.ru','','2026-09-10T14:29:34',NULL,1,1,1);
INSERT INTO employees VALUES(191,'Новый admin1111','last name','email@dfwfw.ru','','2026-09-10T14:29:48',NULL,1,1,1);
INSERT INTO employees VALUES(192,'куапукпукпукп кпукп кп кпкп','','','','2026-09-10T14:29:56+00:00',NULL,1,17,1);
INSERT INTO employees VALUES(193,'string','','','','2026-09-10T14:31:56',NULL,1,0,1);
INSERT INTO employees VALUES(194,'string','','','','2026-09-10T14:32:04',NULL,1,0,1);
INSERT INTO employees VALUES(195,'string','','','','2026-09-10T14:32:27',NULL,1,0,1);
INSERT INTO employees VALUES(196,'string','','','','2026-09-10T14:32:34',NULL,1,1,1);
INSERT INTO employees VALUES(197,'string','','','','2026-09-10T14:32:56',NULL,1,1,1);
INSERT INTO employees VALUES(198,'string','','','','2026-09-10T14:36:43',NULL,1,1,1);
INSERT INTO employees VALUES(199,'rfgwergtrtghrtgh','','','','2026-09-15 14:20:02.897155+00:00',NULL,1,13,0);
INSERT INTO employees VALUES(200,'string','','','','2026-09-15 15:29:01.063413+00:00',NULL,0,1,0);
INSERT INTO employees VALUES(201,'string','','','','2026-09-15 15:29:11.789524+00:00',NULL,0,2,0);
INSERT INTO employees VALUES(202,'string','','','efreferfgerfg','2026-09-15 15:29:19.119610+00:00',NULL,0,2,0);
INSERT INTO employees VALUES(203,'string','','','efreferfgerfg','2026-09-15 15:29:51.660168+00:00',NULL,0,1,0);
INSERT INTO employees VALUES(204,'string','','','efreferfgerfg','2026-09-15 15:34:54.319775+00:00',NULL,0,2,0);
INSERT INTO employees VALUES(205,'string','','','efreferfgerfg','2026-09-15 15:35:10.466856+00:00',NULL,0,2,0);
INSERT INTO employees VALUES(206,'string','','','','2026-09-15 18:35:25.920955+00:00',NULL,1,1,0);
INSERT INTO employees VALUES(207,'string','','','','2026-09-17T16:10:55',NULL,1,1,1);
INSERT INTO employees VALUES(208,'dfwerfewrfgewr','','','','2026-09-17T16:12:08+00:00',NULL,1,4,1);
INSERT INTO employees VALUES(209,'string','','','','2026-09-17T16:27:17',NULL,1,1,1);
CREATE TABLE admins (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    job_title TEXT, 
    department_id INTEGER DEFAULT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
INSERT INTO admins VALUES(122,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(181,'',3);
INSERT INTO admins VALUES(186,'FFf',NULL);
INSERT INTO admins VALUES(187,'FFf',NULL);
INSERT INTO admins VALUES(188,'FFf',NULL);
INSERT INTO admins VALUES(189,'FFf',NULL);
INSERT INTO admins VALUES(190,'FFf',NULL);
INSERT INTO admins VALUES(191,'FFf',NULL);
INSERT INTO admins VALUES(192,'',NULL);
INSERT INTO admins VALUES(193,'',NULL);
INSERT INTO admins VALUES(194,'',NULL);
INSERT INTO admins VALUES(195,'',NULL);
INSERT INTO admins VALUES(196,'',NULL);
INSERT INTO admins VALUES(197,'',NULL);
INSERT INTO admins VALUES(198,'',NULL);
INSERT INTO admins VALUES(207,'',NULL);
INSERT INTO admins VALUES(208,'',3);
INSERT INTO admins VALUES(209,'',3);
CREATE TABLE users (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
);
INSERT INTO users VALUES(182,33);
INSERT INTO users VALUES(183,33);
INSERT INTO users VALUES(184,34);
INSERT INTO users VALUES(185,34);
INSERT INTO users VALUES(199,32);
INSERT INTO users VALUES(200,32);
INSERT INTO users VALUES(201,32);
INSERT INTO users VALUES(202,32);
INSERT INTO users VALUES(203,32);
INSERT INTO users VALUES(204,32);
INSERT INTO users VALUES(205,32);
INSERT INTO users VALUES(206,32);
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	login TEXT,
	password TEXT,
	enabled INTEGER DEFAULT (1),
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO accounts VALUES(170,65,'john_user','537c77bc5f44af2a789aaa5c5df27477036ec34e7a1f1b4ad5f69a38e3c7ea8a',1,'1772824323');
INSERT INTO accounts VALUES(175,70,'login1774880602.1020184','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:23:22');
INSERT INTO accounts VALUES(181,71,'login1774880632.2759092','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:23:52');
INSERT INTO accounts VALUES(188,73,'login1774880632.3632379','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:23:52');
INSERT INTO accounts VALUES(193,74,'login1774880677.939701','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:24:37');
INSERT INTO accounts VALUES(200,76,'login1774880678.0294404','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:24:38');
INSERT INTO accounts VALUES(206,77,'login1774880690.0404623','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:24:50');
INSERT INTO accounts VALUES(213,79,'login1774880690.1236687','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:24:50');
INSERT INTO accounts VALUES(219,80,'login1774880727.9570894','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:25:32');
INSERT INTO accounts VALUES(226,82,'login1774880732.0885665','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:25:32');
INSERT INTO accounts VALUES(232,83,'login1774880814.2065163','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:26:54');
INSERT INTO accounts VALUES(239,85,'login1774880814.294652','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:26:54');
INSERT INTO accounts VALUES(245,86,'login1774880850.7872686','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:27:30');
INSERT INTO accounts VALUES(252,88,'login1774880850.8714156','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:27:30');
INSERT INTO accounts VALUES(258,89,'login1774880859.1478918','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:27:39');
INSERT INTO accounts VALUES(265,91,'login1774880859.2236402','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:27:39');
INSERT INTO accounts VALUES(271,92,'login1774880873.855402','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:27:53');
INSERT INTO accounts VALUES(278,94,'login1774880873.9396765','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:27:53');
INSERT INTO accounts VALUES(284,95,'login1774880911.0611806','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:28:31');
INSERT INTO accounts VALUES(291,97,'login1774880911.137066','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:28:31');
INSERT INTO accounts VALUES(297,98,'login1774881024.2941914','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:30:24');
INSERT INTO accounts VALUES(304,100,'login1774881024.3730721','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:30:24');
INSERT INTO accounts VALUES(310,101,'login1774881116.804021','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:31:56');
INSERT INTO accounts VALUES(317,103,'login1774881116.8849137','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:31:56');
INSERT INTO accounts VALUES(323,104,'login1774881238.460931','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'2026-03-30T17:33:58');
INSERT INTO accounts VALUES(330,106,'login1774881238.5499492','6246707bec8ed96df9cf8e66d1f950e68b587646f19c429c61ee01f7b7ad3800',1,'2026-03-30T17:33:58');
INSERT INTO accounts VALUES(336,107,'login1774884816.7733634','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'1774884818');
INSERT INTO accounts VALUES(338,108,'login1774885312.306541','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'1774885312');
INSERT INTO accounts VALUES(339,109,'login1774885316.7065036','0ecb68654b7fd17640463b33130e0f928633fd53ff6c7a9831622aa1ae7acf0c',1,'1774885316');
INSERT INTO accounts VALUES(340,110,'john.smith','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:30:48');
INSERT INTO accounts VALUES(345,111,'john.smith1775565095.2352347','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:31:35');
INSERT INTO accounts VALUES(351,112,'john.smith1775565115.2233677','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:31:55');
INSERT INTO accounts VALUES(357,113,'john.smith1775565120.6205187','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:32:00');
INSERT INTO accounts VALUES(366,114,'john.smith1775565121.1097398','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:32:01');
INSERT INTO accounts VALUES(375,115,'john.smith1775565129.608966','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:32:09');
INSERT INTO accounts VALUES(384,116,'john.smith1775565189.1279886','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:33:09');
INSERT INTO accounts VALUES(389,117,'john.smith1775565202.2509465','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-04-07T15:33:22');
INSERT INTO accounts VALUES(394,118,'john.smith1775565279.7358196','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'2026-04-07T15:34:39');
INSERT INTO accounts VALUES(397,119,'alice.johnson20260514181346','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'2026-05-14T18:13:46');
INSERT INTO accounts VALUES(400,120,'alice.johnson20260519131525','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'2026-05-19T13:15:25');
INSERT INTO accounts VALUES(403,121,'alice.johnson20260519132656','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'2026-05-19T13:26:56');
INSERT INTO accounts VALUES(406,122,'alice.johnson20260519132927','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-05-19T13:29:27');
INSERT INTO accounts VALUES(410,123,'bob.smith20260519134754','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',0,'1779187674');
INSERT INTO accounts VALUES(412,124,'bob.smith20260519134841','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',0,'1779187721');
INSERT INTO accounts VALUES(415,125,'bob','6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',0,'1779187740');
INSERT INTO accounts VALUES(420,126,'bob.smith20260519144710','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',0,'1779191271');
INSERT INTO accounts VALUES(422,127,'bob.smith20260519145452','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',0,'2026-05-19T14:54:52');
INSERT INTO accounts VALUES(427,128,'login','e5c423e29a981dd8149066bebe675f3979fb9c7f1cbe97db92604ccbbeba4493',1,'2026-05-28T15:01:24');
INSERT INTO accounts VALUES(429,131,'login-string','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T14:53:50');
INSERT INTO accounts VALUES(431,132,'login-string1','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T15:37:45');
INSERT INTO accounts VALUES(433,133,'login-string11','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T15:43:01');
INSERT INTO accounts VALUES(435,137,'логин','1bd627127cd59de4669ce89386e2180cd63f61af5b59045329545a2f197c981b',1,'2026-06-01T15:45:56');
INSERT INTO accounts VALUES(441,138,'string1111111111111111112111111111111','5797a9aba74864f5f0876523d4e63dd83298be2fe3c50eb4711cbb981ddb200f',1,'2026-06-01T17:11:09');
INSERT INTO accounts VALUES(447,142,'login-user','1bd627127cd59de4669ce89386e2180cd63f61af5b59045329545a2f197c981b',0,'2026-06-01T17:24:48');
INSERT INTO accounts VALUES(455,147,'login-new1010','409d93026fcb52ae62a8d9c892f49054a3718eca11ce14e87a95b2ec06f4e509',1,'2026-06-04T16:00:02');
INSERT INTO accounts VALUES(466,160,'login10','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-08T17:39:36');
INSERT INTO accounts VALUES(468,161,'login11','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-08T17:42:23');
INSERT INTO accounts VALUES(471,164,'string-login','e530f300120d9ba00f9d79b092aadd36ab4c2bfb96a6a995e8a479fdc2b0726f',0,'2026-06-08T18:11:46');
INSERT INTO accounts VALUES(472,166,'login-u','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',0,'2026-06-09T13:32:06');
INSERT INTO accounts VALUES(474,167,'login-user1','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',0,'2026-06-09T13:34:48');
INSERT INTO accounts VALUES(476,168,'login-admin','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:35:41');
INSERT INTO accounts VALUES(477,169,'login-admin1','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:36:45');
INSERT INTO accounts VALUES(483,170,'htyhyrujujuj','ff7bd97b1a7789ddd2775122fd6817f3173672da9f802ceec57f284325bf589f',1,'2026-06-09T17:28:30');
INSERT INTO accounts VALUES(485,172,'erfertgrtg','ff7bd97b1a7789ddd2775122fd6817f3173672da9f802ceec57f284325bf589f',0,'2026-06-09T17:38:04');
INSERT INTO accounts VALUES(505,173,'login111111','4d064ebb8c9df20d2a71d3222f730c90823e333476805f0bcbd05c40d1f58e07',1,'2026-07-29T15:14:23');
INSERT INTO accounts VALUES(506,174,'аккаунт','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',0,'2026-07-29T15:20:49');
INSERT INTO accounts VALUES(507,176,'логин123','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-07-29T15:39:45');
INSERT INTO accounts VALUES(520,177,'bl','c01939912c9794c982e3c5c1c14f53af40e2047ceea5535d831e1a6e90898f18',0,'2026-09-04 17:03:37.710131+00:00');
INSERT INTO accounts VALUES(522,178,'login123456','e9e9826f25a049f5957379c654218ef7c5bf2e7f38db1ee7f8451fce28b18694',1,'2026-09-07 17:03:11.582497+00:00');
INSERT INTO accounts VALUES(523,179,'login12345611111111','e9e9826f25a049f5957379c654218ef7c5bf2e7f38db1ee7f8451fce28b18694',1,'2026-09-07T17:04:10');
INSERT INTO accounts VALUES(524,180,'login25','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-07 17:50:35.572638+00:00');
INSERT INTO accounts VALUES(525,181,'tega','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-08T14:11:07');
INSERT INTO accounts VALUES(528,186,'login-new1','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-09T18:15:07');
INSERT INTO accounts VALUES(530,187,'login-new11','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-10T14:28:51');
INSERT INTO accounts VALUES(534,192,'string-login12','8ab011ebc3530407f7a3eecade4c4a5772693233341aee1cfead0bdbd99f5f7d',1,'2026-09-10T14:47:30');
INSERT INTO accounts VALUES(546,199,'userclient32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-15 14:20:02.897326+00:00');
INSERT INTO accounts VALUES(548,204,'user1client32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',0,'2026-09-15 15:34:54.319818+00:00');
INSERT INTO accounts VALUES(550,205,'user2client32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',0,'2026-09-15 15:35:10.466892+00:00');
INSERT INTO accounts VALUES(566,206,'string111111111111111111111111111111111111','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-15 18:35:25.920997+00:00');
CREATE TABLE clients (
	client_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	name TEXT,
	address TEXT,
	email TEXT,
	phone TEXT,
	enabled INTEGER, version INTEGER DEFAULT 0,
	date_created TEXT, description TEXT DEFAULT (''),
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO clients VALUES(32,181,'Клиент','','','',1,3,'2026-09-08T14:13:04.962258','');
INSERT INTO clients VALUES(33,181,'Клиент новый','ацукаукапукап','','',1,7,'2026-09-08T14:16:17.964453','');
INSERT INTO clients VALUES(34,122,'Клиент новый новый','','','',1,1,'2026-09-09T12:45:02.670365','Там нет Новичихина');
INSERT INTO clients VALUES(35,122,'Клиент 2','','','',1,0,'2026-09-09T13:49:44.420454','');
INSERT INTO clients VALUES(36,122,'Клиент 2','','','уацукацка',1,0,'2026-09-09T13:50:55.389754','');
INSERT INTO clients VALUES(37,122,'Новый клиент','','rtrtgt@dfvefverfgv.rgtgrt','',1,1,'2026-09-16T12:47:42.789949','');
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER DEFAULT 0);
INSERT INTO roles VALUES(5,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.view, role.assign, role.revoke','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(60,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.view, role.assign, role.revoke','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(61,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:21:42+00:00',0,0);
INSERT INTO roles VALUES(62,'Super Admin','role.assign,admin.view','Full system access',1,'2026-03-23T12:22:06+00:00',1,0);
INSERT INTO roles VALUES(63,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:22:06+00:00',0,0);
INSERT INTO roles VALUES(64,'Super Admin','role.assign,admin.view','Full system access',1,'2026-03-23T12:22:34+00:00',1,0);
INSERT INTO roles VALUES(66,'Super Admin','role.assign,admin.view','Full system access',1,'2026-03-23T12:22:49+00:00',1,0);
INSERT INTO roles VALUES(67,'Can accepted','ticket.accepted','ticket.accepted',0,NULL,1,NULL);
INSERT INTO roles VALUES(68,'string','client.operation','fwfwrfrweferf',0,'2026-07-30T11:49:45+00:00',1,0);
INSERT INTO roles VALUES(69,'string','client.view,ticket.view','ewrfwrfwerfger',0,'2026-09-17T12:47:36+00:00',1,0);
INSERT INTO roles VALUES(70,'string','ticket.view','efwrfrwef',0,'2026-09-17T12:48:36+00:00',0,0);
CREATE TABLE admins_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO admins_roles VALUES(122,67);
INSERT INTO admins_roles VALUES(122,5);
INSERT INTO admins_roles VALUES(186,5);
INSERT INTO admins_roles VALUES(187,5);
INSERT INTO admins_roles VALUES(188,5);
INSERT INTO admins_roles VALUES(189,5);
INSERT INTO admins_roles VALUES(190,5);
INSERT INTO admins_roles VALUES(191,5);
INSERT INTO admins_roles VALUES(196,5);
INSERT INTO admins_roles VALUES(197,67);
INSERT INTO admins_roles VALUES(197,5);
INSERT INTO admins_roles VALUES(198,67);
INSERT INTO admins_roles VALUES(198,5);
INSERT INTO admins_roles VALUES(181,5);
INSERT INTO admins_roles VALUES(207,5);
INSERT INTO admins_roles VALUES(208,5);
INSERT INTO admins_roles VALUES(209,5);
CREATE TABLE users_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO users_roles VALUES(8,61);
INSERT INTO users_roles VALUES(67,61);
INSERT INTO users_roles VALUES(123,63);
INSERT INTO users_roles VALUES(124,63);
INSERT INTO users_roles VALUES(125,63);
INSERT INTO users_roles VALUES(126,63);
INSERT INTO users_roles VALUES(127,63);
INSERT INTO users_roles VALUES(140,65);
INSERT INTO users_roles VALUES(141,65);
INSERT INTO users_roles VALUES(142,65);
INSERT INTO users_roles VALUES(165,61);
INSERT INTO users_roles VALUES(166,61);
INSERT INTO users_roles VALUES(167,61);
INSERT INTO users_roles VALUES(172,61);
INSERT INTO users_roles VALUES(172,63);
INSERT INTO users_roles VALUES(201,61);
INSERT INTO users_roles VALUES(202,61);
INSERT INTO users_roles VALUES(204,61);
INSERT INTO users_roles VALUES(205,61);
INSERT INTO users_roles VALUES(199,61);
INSERT INTO users_roles VALUES(206,61);
CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
INSERT INTO user_tickets_comment VALUES(3,13,199,'comment1','2026-09-15T15:31:58.908792+00:00');
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT, comment TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO user_tickets_status_record VALUES(18,182,9,'created','2026-09-08T11:22:31.517291+00:00','');
INSERT INTO user_tickets_status_record VALUES(19,122,9,'confirmed_by_admin','2026-09-08T11:22:31.517328+00:00','');
INSERT INTO user_tickets_status_record VALUES(20,184,10,'created','2026-09-09T09:48:17.888599+00:00','');
INSERT INTO user_tickets_status_record VALUES(21,122,10,'confirmed_by_admin','2026-09-09T09:48:17.888641+00:00','');
INSERT INTO user_tickets_status_record VALUES(22,122,10,'in_work','2026-09-09T09:48:54.293702+00:00','');
INSERT INTO user_tickets_status_record VALUES(23,122,10,'confirmed_by_admin','2026-09-09T09:49:22.644530+00:00','Мы пока думаем');
INSERT INTO user_tickets_status_record VALUES(24,122,10,'in_work','2026-09-09T09:49:35.635219+00:00','Мы пока думаем');
INSERT INTO user_tickets_status_record VALUES(25,122,10,'confirmed_by_admin','2026-09-09T09:51:47.331020+00:00','На следующие выезд захватить бизнес-тренера');
INSERT INTO user_tickets_status_record VALUES(26,122,10,'in_work','2026-09-09T09:51:58.244206+00:00','На следующие выезд захватить бизнес-тренера');
INSERT INTO user_tickets_status_record VALUES(27,122,10,'waiting_for_confirmation','2026-09-09T09:53:31.407351+00:00','');
INSERT INTO user_tickets_status_record VALUES(28,122,10,'execution_confirmed_by_admin','2026-09-09T09:54:02.785926+00:00','');
INSERT INTO user_tickets_status_record VALUES(29,199,11,'created','2026-09-15T11:58:24.551541+00:00','');
INSERT INTO user_tickets_status_record VALUES(30,199,12,'created','2026-09-15T15:31:48.119684+00:00','');
INSERT INTO user_tickets_status_record VALUES(31,122,12,'confirmed_by_admin','2026-09-15T15:31:48.119721+00:00','');
INSERT INTO user_tickets_status_record VALUES(32,199,13,'created','2026-09-15T15:31:58.908792+00:00','');
INSERT INTO user_tickets_status_record VALUES(33,122,13,'confirmed_by_admin','2026-09-15T15:31:58.908837+00:00','comment1');
CREATE TABLE user_tickets_executor_assignments (
	user_executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	admin_id INTEGER,
	date_assignment TEXT,
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- заявки от какого клиента
	user_id INTEGER, -- кто создал заявку
	user_ticket_contact_user_id INTEGER DEFAULT NULL, -- контактное лицо по заявке, может не быть
	text_of_ticket TEXT, -- текст заявки 
	date_created TEXT,
	version INTEGER DEFAULT 0,
	date_closed TEXT, -- дата завершения или снятия заявки 
	is_closed INTEGER, description TEXT, urgency_level INTEGER DEFAULT (0) NOT NULL,
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO user_tickets VALUES(9,33,182,NULL,'Настроить принтер','2026-09-08T11:22:31.517291+00:00',1,NULL,0,'Принтер новый',0);
INSERT INTO user_tickets VALUES(10,34,184,184,'расскажите, почему вы считаете меня дураком?','2026-09-09T09:48:17.888599+00:00',8,'2026-09-09T09:54:02.785926+00:00',1,'Надо набрать статистику',0);
INSERT INTO user_tickets VALUES(11,32,199,NULL,'string','2026-09-15T11:58:24.551541+00:00',0,NULL,0,'ампуапмепмпм',0);
INSERT INTO user_tickets VALUES(12,32,199,NULL,'string','2026-09-15T15:31:48.119684+00:00',0,NULL,0,'',0);
INSERT INTO user_tickets VALUES(13,32,199,NULL,'string','2026-09-15T15:31:58.908792+00:00',0,NULL,0,'',0);
CREATE TABLE ticket_comments (
    ticket_comment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticket_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,

    comment TEXT NOT NULL,
    date_created TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE,

    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT
);
INSERT INTO ticket_comments VALUES(4,10,122,'Комментарий','2026-09-08T11:26:21.723596+00:00');
INSERT INTO ticket_comments VALUES(5,12,122,'На следующие выезд захватить бизнес-тренера','2026-09-09T09:51:27.190503+00:00');
INSERT INTO ticket_comments VALUES(6,15,122,'comment1','2026-09-15T15:31:58.910575+00:00');
INSERT INTO ticket_comments VALUES(7,16,122,'jm uil;.','2026-09-16T09:48:49.833694+00:00');
CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    admin_id INTEGER,
    user_id INTEGER NULL,
    contact_user_id INTEGER NULL,
    user_ticket_id INTEGER NULL,

    department_id INTEGER NULL,

    text_of_ticket TEXT NOT NULL,
    description TEXT NULL,

    date_created TEXT NOT NULL,

    is_remote INTEGER NOT NULL DEFAULT 0
        CHECK (is_remote IN (0, 1)),

    urgency_level INTEGER NOT NULL DEFAULT 0,

    version INTEGER DEFAULT 0,

    FOREIGN KEY (client_id)
        REFERENCES clients(client_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (admin_id)
        REFERENCES admins(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_id)
        REFERENCES users(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (contact_user_id)
        REFERENCES users(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (user_ticket_id)
        REFERENCES user_tickets(user_ticket_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE RESTRICT
);
INSERT INTO tickets VALUES(10,32,181,NULL,NULL,NULL,2,'Настроить принтер','Принтер новый','2026-09-08T11:21:06.712174+00:00',0,1,14);
INSERT INTO tickets VALUES(11,33,122,182,NULL,9,2,'Настроить принтер','Принтер новый','2026-09-08T11:22:31.517626+00:00',0,0,3);
INSERT INTO tickets VALUES(12,34,122,184,184,10,2,'расскажите, почему вы считаете меня дураком?','Надо набрать статистику','2026-09-09T09:48:17.888943+00:00',0,0,13);
INSERT INTO tickets VALUES(13,32,NULL,199,NULL,11,NULL,'string','ампуапмепмпм','2026-09-15T11:58:24.551541+00:00',0,0,1);
INSERT INTO tickets VALUES(14,32,122,199,NULL,12,NULL,'string',NULL,'2026-09-15T15:31:48.121220+00:00',0,0,0);
INSERT INTO tickets VALUES(15,32,122,199,NULL,13,NULL,'string',NULL,'2026-09-15T15:31:58.910575+00:00',0,0,0);
INSERT INTO tickets VALUES(16,37,122,NULL,NULL,NULL,2,'string',NULL,'2026-09-16T09:48:49.833694+00:00',0,0,0);
INSERT INTO tickets VALUES(17,37,181,NULL,NULL,NULL,2,'string','вуамуамуацмуам','2026-09-16T10:46:20.126014+00:00',0,0,9);
INSERT INTO tickets VALUES(18,37,122,NULL,NULL,NULL,2,'string','fvef fe g','2026-09-16T11:14:04.565507+00:00',0,0,0);
INSERT INTO tickets VALUES(19,37,122,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-16T12:01:00.791839+00:00',0,0,2);
INSERT INTO tickets VALUES(20,37,122,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-16T12:03:54.370354+00:00',0,0,2);
CREATE TABLE ticket_status_records (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    actor_employee_id INTEGER NULL,
    status TEXT NOT NULL,
    date_created TEXT NOT NULL,
    executor_id INTEGER NULL,
    planned_start_at TEXT NULL,
    planned_finish_at TEXT NULL,
    actual_started_at TEXT NULL,
    actual_finished_at TEXT NULL,
    comment TEXT NOT NULL DEFAULT '',

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE,

    FOREIGN KEY (actor_employee_id)
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (executor_id)
        REFERENCES admins(employee_id)
        ON DELETE RESTRICT
);
INSERT INTO ticket_status_records VALUES(46,10,181,'created','2026-09-08T11:21:06.712174+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(47,11,122,'created','2026-09-08T11:22:31.517626+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(48,11,122,'accepted','2026-09-08T11:22:31.517677+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(49,10,122,'accepted','2026-09-08T11:23:41.695436+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(50,10,122,'scheduled','2026-09-08T11:24:10.329183+00:00',NULL,'2026-09-08T11:24:00+00:00',NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(51,10,122,'scheduled','2026-09-08T11:24:25.845771+00:00',NULL,'2026-09-08T11:24:00+00:00',NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(52,10,122,'assigned','2026-09-08T11:24:43.767104+00:00',122,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(53,10,122,'at_work','2026-09-08T11:24:50.871218+00:00',122,NULL,NULL,'2026-09-08T11:24:50.871218+00:00',NULL,'');
INSERT INTO ticket_status_records VALUES(54,10,122,'paused','2026-09-08T11:24:58.883317+00:00',122,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(55,10,122,'assigned','2026-09-08T11:25:24.645916+00:00',122,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(56,10,122,'assigned','2026-09-08T11:25:35.882793+00:00',122,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(57,10,122,'accepted','2026-09-08T11:26:38.132384+00:00',NULL,NULL,NULL,NULL,NULL,'Комментарий');
INSERT INTO ticket_status_records VALUES(58,10,122,'deferred','2026-09-08T11:27:29.143392+00:00',NULL,NULL,NULL,NULL,NULL,'Комментарий отложено');
INSERT INTO ticket_status_records VALUES(59,10,122,'accepted','2026-09-08T11:32:36.058239+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(60,10,122,'assigned','2026-09-08T11:32:40.328693+00:00',181,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(61,11,122,'deferred','2026-09-08T11:40:02.257529+00:00',NULL,NULL,NULL,NULL,NULL,'Client disabled');
INSERT INTO ticket_status_records VALUES(62,12,122,'created','2026-09-09T09:48:17.888943+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(63,12,122,'accepted','2026-09-09T09:48:17.888990+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(64,12,122,'assigned','2026-09-09T09:48:54.293506+00:00',181,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(65,12,122,'accepted','2026-09-09T09:49:22.644316+00:00',NULL,NULL,NULL,NULL,NULL,'Мы пока думаем');
INSERT INTO ticket_status_records VALUES(66,12,122,'deferred','2026-09-09T09:49:35.634993+00:00',NULL,NULL,NULL,NULL,NULL,'Мы пока думаем');
INSERT INTO ticket_status_records VALUES(67,12,122,'accepted','2026-09-09T09:51:47.330816+00:00',NULL,NULL,NULL,NULL,NULL,'На следующие выезд захватить бизнес-тренера');
INSERT INTO ticket_status_records VALUES(68,12,122,'assigned','2026-09-09T09:51:58.243980+00:00',181,NULL,NULL,NULL,NULL,'На следующие выезд захватить бизнес-тренера');
INSERT INTO ticket_status_records VALUES(69,12,122,'assigned','2026-09-09T09:52:14.059304+00:00',122,NULL,NULL,NULL,NULL,'На следующие выезд захватить бизнес-тренера');
INSERT INTO ticket_status_records VALUES(70,12,122,'at_work','2026-09-09T09:52:17.913301+00:00',122,NULL,NULL,'2026-09-09T09:52:17.913301+00:00',NULL,'На следующие выезд захватить бизнес-тренера');
INSERT INTO ticket_status_records VALUES(71,12,122,'paused','2026-09-09T09:52:25.043878+00:00',122,NULL,NULL,NULL,NULL,'На следующие выезд захватить бизнес-тренера');
INSERT INTO ticket_status_records VALUES(72,12,122,'at_work','2026-09-09T09:53:02.186999+00:00',122,NULL,NULL,'2026-09-09T09:53:02.186999+00:00',NULL,'');
INSERT INTO ticket_status_records VALUES(73,12,122,'ready_for_review','2026-09-09T09:53:31.407125+00:00',122,NULL,NULL,NULL,'2026-09-09T09:53:31.407125+00:00','');
INSERT INTO ticket_status_records VALUES(74,12,122,'executed','2026-09-09T09:54:02.785644+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(75,13,NULL,'created_from_ticket_user','2026-09-15T11:58:24.551541+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(76,13,NULL,'cancelled_by_user','2026-09-15T12:08:49.925451+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(77,10,122,'deferred','2026-09-15T12:47:24.556687+00:00',NULL,NULL,NULL,NULL,NULL,'Client disabled');
INSERT INTO ticket_status_records VALUES(78,14,122,'created','2026-09-15T15:31:48.121220+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(79,14,122,'accepted','2026-09-15T15:31:48.121293+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(80,15,122,'created','2026-09-15T15:31:58.910575+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(81,15,122,'accepted','2026-09-15T15:31:58.910654+00:00',NULL,NULL,NULL,NULL,NULL,'comment1');
INSERT INTO ticket_status_records VALUES(82,16,122,'created','2026-09-16T09:48:49.833694+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(83,16,122,'accepted','2026-09-16T09:48:49.833760+00:00',NULL,NULL,NULL,NULL,NULL,'jm uil;.');
INSERT INTO ticket_status_records VALUES(84,17,181,'created','2026-09-16T10:46:20.126014+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(85,18,122,'created','2026-09-16T11:14:04.565507+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(86,18,122,'accepted','2026-09-16T11:14:04.565540+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(87,17,122,'accepted','2026-09-16T11:15:01.389216+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(88,17,122,'deferred','2026-09-16T11:29:33.812214+00:00',NULL,NULL,NULL,NULL,NULL,'string');
INSERT INTO ticket_status_records VALUES(89,17,122,'scheduled','2026-09-16T11:38:34.499488+00:00',NULL,'2025-09-16T11:36:40.255000+00:00','2026-09-16T11:36:40.255000+00:00',NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(90,17,122,'scheduled','2026-09-16T11:39:11.565138+00:00',NULL,'2026-09-17T11:36:40.255000+00:00','2026-09-18T11:36:40.255000+00:00',NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(91,17,122,'assigned','2026-09-16T11:56:41.361244+00:00',181,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(92,17,122,'deferred','2026-09-16T11:58:55.171285+00:00',NULL,NULL,NULL,NULL,NULL,'string');
INSERT INTO ticket_status_records VALUES(93,17,122,'scheduled','2026-09-16T12:00:20.250291+00:00',NULL,'2026-09-17T11:36:40.255000+00:00','2026-09-18T11:36:40.255000+00:00',NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(94,19,122,'created','2026-09-16T12:01:00.791839+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(95,19,122,'accepted','2026-09-16T12:01:00.791872+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(96,19,122,'scheduled','2026-09-16T12:01:19.252999+00:00',NULL,'2026-09-17T11:36:40.255000+00:00','2026-09-18T11:36:40.255000+00:00',NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(97,19,122,'ready_to_work','2026-09-16T12:03:27.546783+00:00',181,'2026-09-16T12:03:17.153000+00:00','2026-09-16T12:03:17.153000+00:00',NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(98,20,122,'created','2026-09-16T12:03:54.370354+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(99,20,122,'accepted','2026-09-16T12:03:54.370388+00:00',NULL,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(100,20,122,'assigned','2026-09-16T12:05:39.640295+00:00',122,NULL,NULL,NULL,NULL,'');
INSERT INTO ticket_status_records VALUES(101,20,122,'at_work','2026-09-16T12:05:51.096456+00:00',122,NULL,NULL,'2026-09-16T12:05:51.096456+00:00',NULL,'');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',209);
INSERT INTO sqlite_sequence VALUES('accounts',569);
INSERT INTO sqlite_sequence VALUES('roles',70);
INSERT INTO sqlite_sequence VALUES('clients',37);
INSERT INTO sqlite_sequence VALUES('user_tickets',13);
INSERT INTO sqlite_sequence VALUES('user_tickets_status_record',33);
INSERT INTO sqlite_sequence VALUES('user_tickets_comment',3);
INSERT INTO sqlite_sequence VALUES('departments',7);
INSERT INTO sqlite_sequence VALUES('tickets',20);
INSERT INTO sqlite_sequence VALUES('ticket_status_records',101);
INSERT INTO sqlite_sequence VALUES('ticket_comments',7);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
CREATE UNIQUE INDEX idx_departments_name
ON departments(name);
CREATE INDEX idx_ticket_comments_ticket_id
ON ticket_comments(ticket_id, ticket_comment_id);
CREATE INDEX idx_ticket_comments_employee_id
ON ticket_comments(employee_id);
COMMIT;

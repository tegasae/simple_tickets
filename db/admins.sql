PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE departments (
    department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    version INTEGER DEFAULT 0,
    date_created TEXT
);
INSERT INTO departments VALUES(2,'Суппорт',1,2,'2026-07-27T16:02:50.257132');
INSERT INTO departments VALUES(3,'1С',1,4,'2026-07-27T16:03:05.569976');
INSERT INTO departments VALUES(5,'Веб',1,1,'2026-09-07T17:04:25.825200');
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
INSERT INTO employees VALUES(184,'Роман','Новичихин','','','2026-09-09 12:45:17.526999+00:00',NULL,1,4,0);
INSERT INTO employees VALUES(192,'куапукпукпукп кпукп кп кпкп','','','','2026-09-10T14:29:56+00:00',NULL,1,17,1);
INSERT INTO employees VALUES(193,'string','','','','2026-09-10T14:31:56',NULL,1,0,1);
INSERT INTO employees VALUES(194,'string','','','','2026-09-10T14:32:04',NULL,1,0,1);
INSERT INTO employees VALUES(195,'string','','','','2026-09-10T14:32:27',NULL,1,0,1);
INSERT INTO employees VALUES(196,'string','','','','2026-09-10T14:32:34',NULL,1,1,1);
INSERT INTO employees VALUES(197,'string','','','','2026-09-10T14:32:56',NULL,1,1,1);
INSERT INTO employees VALUES(198,'string','','','','2026-09-10T14:36:43',NULL,1,1,1);
INSERT INTO employees VALUES(199,'Пользователь 1','','','','2026-09-15 14:20:02.897155+00:00',NULL,1,14,0);
INSERT INTO employees VALUES(200,'Пользователь 2','','','','2026-09-15 15:29:01.063413+00:00',NULL,1,3,0);
INSERT INTO employees VALUES(207,'string','','','','2026-09-17T16:10:55',NULL,1,1,1);
INSERT INTO employees VALUES(208,'dfwerfewrfgewr','','','','2026-09-17T16:12:08+00:00',NULL,1,4,1);
INSERT INTO employees VALUES(209,'string','','','','2026-09-17T16:27:17',NULL,1,1,1);
INSERT INTO employees VALUES(210,'Пользователь 1 клиента 2','','','','2026-10-01 18:41:33.728954+00:00',NULL,1,1,0);
INSERT INTO employees VALUES(211,'Пользователь 2 Клиента 2','','','','2026-10-01 18:41:54.906240+00:00',NULL,1,1,0);
CREATE TABLE admins (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    job_title TEXT, 
    department_id INTEGER DEFAULT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
INSERT INTO admins VALUES(122,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(181,'',3);
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
INSERT INTO users VALUES(184,34);
INSERT INTO users VALUES(199,32);
INSERT INTO users VALUES(200,32);
INSERT INTO users VALUES(210,36);
INSERT INTO users VALUES(211,36);
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
INSERT INTO accounts VALUES(534,192,'string-login12','8ab011ebc3530407f7a3eecade4c4a5772693233341aee1cfead0bdbd99f5f7d',1,'2026-09-10T14:47:30');
INSERT INTO accounts VALUES(546,199,'userclient32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-15 14:20:02.897326+00:00');
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
INSERT INTO clients VALUES(32,181,'Клиент 1','','','',1,7,'2026-09-08T14:13:04.962258','');
INSERT INTO clients VALUES(34,122,'Клиент даже не знаю как назвать','','','',1,2,'2026-09-09T12:45:02.670365','Не совсем обычный клиент');
INSERT INTO clients VALUES(36,122,'Клиент 2','','','Телефон',1,12,'2026-09-09T13:50:55.389754','Обычный клиент');
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER DEFAULT 0);
INSERT INTO roles VALUES(5,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.created, ticket.view, ticket.accepted, ticket.at_work, ticket.at_work_remote, ticket.at_work_retrospective, ticket.canceled, ticket.executed, role.assign, role_user.assign','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(60,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.created, ticket.view, ticket.accepted, ticket.at_work, ticket.at_work_remote, ticket.at_work_retrospective, ticket.canceled, ticket.executed, role.assign, role_user.assign','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
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
INSERT INTO users_roles VALUES(199,61);
INSERT INTO users_roles VALUES(210,61);
INSERT INTO users_roles VALUES(210,63);
INSERT INTO users_roles VALUES(211,61);
INSERT INTO users_roles VALUES(211,63);
CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	actor_employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT, comment TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (actor_employee_id) REFERENCES employees(employee_id) on delete restrict
);
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
INSERT INTO ticket_comments VALUES(8,3,181,'fergferg','2026-09-30T19:40:44.861466+00:00');
INSERT INTO ticket_comments VALUES(9,4,181,'fergferg','2026-09-30T19:41:59.381170+00:00');
INSERT INTO ticket_comments VALUES(10,5,181,'укукака','2026-10-01T13:31:42.525384+00:00');
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- заявки от какого клиента
	user_id INTEGER, -- кто создал заявку
	contact_user_id INTEGER DEFAULT NULL, -- контактное лицо по заявке, может не быть
	text_of_ticket TEXT, -- текст заявки 
	date_created TEXT,
	version INTEGER DEFAULT 0,
	date_finished TEXT DEFAULT NULL, description TEXT, -- дата завершения или снятия заявки 
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (contact_user_id) REFERENCES employees(employee_id) on delete restrict
);
CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    user_id INTEGER NULL,
    contact_user_id INTEGER NULL,
    user_ticket_id INTEGER NULL,
    department_id INTEGER NULL,
    text_of_ticket TEXT,
    description TEXT NULL,
    date_created TEXT NOT NULL,
    remote_work_recommended INTEGER NOT NULL DEFAULT 0 CHECK (remote_work_recommended IN (0, 1)),
	planned_at TEXT,
    urgency_level INTEGER NOT NULL DEFAULT 0,
	current_executor_id INTEGER DEFAULT 0,
	date_finished TEXT NULL,
    version INTEGER DEFAULT 0,
    FOREIGN KEY (client_id)
        REFERENCES clients(client_id)
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
INSERT INTO tickets VALUES(1,36,NULL,NULL,NULL,3,'string',NULL,'2026-09-30T19:14:58.390803+00:00',0,NULL,'normal',0,NULL,0);
INSERT INTO tickets VALUES(2,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-30T19:40:27.310056+00:00',0,'2026-10-01T12:00:00+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(3,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-30T19:40:44.861466+00:00',0,'2026-10-01T12:00:00+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(4,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-30T19:41:59.381170+00:00',0,'2026-10-01T12:00:00+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(5,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T13:30:22.571755+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,'2026-10-01T14:16:45.787360+00:00',11);
INSERT INTO tickets VALUES(6,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-10-01T14:18:02.727712+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,'2026-10-01T14:21:52.567390+00:00',2);
INSERT INTO tickets VALUES(7,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:15.345594+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',181,NULL,2);
INSERT INTO tickets VALUES(8,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:35.006642+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,NULL,0);
CREATE TABLE ticket_status_records (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    actor_employee_id INTEGER NULL,
    status TEXT NOT NULL,
    date_created TEXT NOT NULL,
    executor_id INTEGER NULL,
    actual_started_at TEXT NULL,
    actual_finished_at TEXT NULL,
    work_is_remote INTEGER DEFAULT 0 CHECK (work_is_remote IN (0, 1)),
    comment TEXT NOT NULL DEFAULT '', duration INTEGER,

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
INSERT INTO ticket_status_records VALUES(1,1,181,'created','2026-09-30T19:14:58.390803+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(2,1,181,'accepted','2026-09-30T19:14:58.390984+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(3,2,181,'created','2026-09-30T19:40:27.310056+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(4,2,181,'accepted','2026-09-30T19:40:27.310240+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(5,3,181,'created','2026-09-30T19:40:44.861466+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(6,3,181,'accepted','2026-09-30T19:40:44.861684+00:00',NULL,NULL,NULL,NULL,'fergferg',0);
INSERT INTO ticket_status_records VALUES(7,4,181,'created','2026-09-30T19:41:59.381170+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(8,4,181,'accepted','2026-09-30T19:41:59.381423+00:00',NULL,NULL,NULL,NULL,'fergferg',0);
INSERT INTO ticket_status_records VALUES(9,5,181,'created','2026-10-01T13:30:22.571755+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(10,5,181,'accepted','2026-10-01T13:30:22.571881+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(11,5,181,'deferred','2026-10-01T13:32:34.928571+00:00',NULL,NULL,NULL,NULL,'string',0);
INSERT INTO ticket_status_records VALUES(12,5,181,'assigned','2026-10-01T13:35:19.933224+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(13,5,181,'accepted','2026-10-01T13:35:44.728090+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(14,5,181,'assigned','2026-10-01T13:36:27.499376+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(15,5,181,'assigned','2026-10-01T13:38:03.672245+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(16,5,181,'at_work','2026-10-01T13:42:23.878531+00:00',0,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(17,5,181,'paused','2026-10-01T13:53:45.017393+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(18,5,181,'at_work','2026-10-01T14:13:34.431025+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(19,5,181,'ready_for_review','2026-10-01T14:16:45.787148+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(20,5,181,'executed','2026-10-01T14:16:45.787360+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(21,6,181,'created','2026-10-01T14:18:02.727712+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(22,6,181,'accepted','2026-10-01T14:18:02.727981+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(23,6,181,'assigned','2026-10-01T14:19:04.877698+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(24,6,181,'at_work','2026-10-01T14:21:52.567082+00:00',NULL,NULL,NULL,0,'',1000);
INSERT INTO ticket_status_records VALUES(25,6,181,'ready_for_review','2026-10-01T14:21:52.567082+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(26,6,181,'executed','2026-10-01T14:21:52.567390+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(27,7,181,'created','2026-10-01T14:42:15.345594+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(28,7,181,'accepted','2026-10-01T14:42:15.345727+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(29,8,181,'created','2026-10-01T14:42:35.006642+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(30,8,181,'accepted','2026-10-01T14:42:35.006757+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(31,7,181,'assigned','2026-10-01T14:43:22.812114+00:00',181,NULL,NULL,NULL,'',0);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',211);
INSERT INTO sqlite_sequence VALUES('accounts',570);
INSERT INTO sqlite_sequence VALUES('roles',70);
INSERT INTO sqlite_sequence VALUES('clients',37);
INSERT INTO sqlite_sequence VALUES('user_tickets_status_record',33);
INSERT INTO sqlite_sequence VALUES('user_tickets_comment',3);
INSERT INTO sqlite_sequence VALUES('departments',7);
INSERT INTO sqlite_sequence VALUES('ticket_comments',10);
INSERT INTO sqlite_sequence VALUES('tickets',8);
INSERT INTO sqlite_sequence VALUES('ticket_status_records',31);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
CREATE UNIQUE INDEX idx_departments_name
ON departments(name);
CREATE INDEX idx_ticket_comments_ticket_id
ON ticket_comments(ticket_id, ticket_comment_id);
CREATE INDEX idx_ticket_comments_employee_id
ON ticket_comments(employee_id);
COMMIT;

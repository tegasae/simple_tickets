PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE departments (
    department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    version INTEGER DEFAULT 0,
    date_created TEXT
);
INSERT INTO departments VALUES(2,'Суппорт',1,25,'2026-07-27T16:02:50.257132');
INSERT INTO departments VALUES(3,'1С',1,8,'2026-07-27T16:03:05.569976');
INSERT INTO departments VALUES(5,'Веб',1,3,'2026-09-07T17:04:25.825200');
INSERT INTO departments VALUES(8,'efref',1,4,'2026-10-06T17:32:04.774745');
INSERT INTO departments VALUES(9,'1111',1,2,'2026-10-09T15:45:59.820438');
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
INSERT INTO employees VALUES(122,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19T13:29:27+00:00',NULL,1,10,1);
INSERT INTO employees VALUES(181,'Тэга','','','','2026-09-08T14:11:07+00:00',NULL,1,15,1);
INSERT INTO employees VALUES(184,'Роман','Новичихин','','','2026-09-09 12:45:17.526999+00:00',NULL,0,5,0);
INSERT INTO employees VALUES(199,'Пользователь 1','','','','2026-09-15 14:20:02.897155+00:00',NULL,0,19,0);
INSERT INTO employees VALUES(200,'Пользователь 2','','','','2026-09-15 15:29:01.063413+00:00',NULL,0,4,0);
INSERT INTO employees VALUES(210,'Пользователь 1 клиента 2','','','','2026-10-01 18:41:33.728954+00:00',NULL,1,16,0);
INSERT INTO employees VALUES(211,'Пользователь 2 Клиента 2','','','','2026-10-01 18:41:54.906240+00:00',NULL,0,5,0);
INSERT INTO employees VALUES(212,'Пользователь клиента 3','','','','2026-10-01 21:22:37.069747+00:00',NULL,1,2,0);
INSERT INTO employees VALUES(216,'efwef','','','','2026-10-05T15:27:46+00:00',NULL,1,1,1);
INSERT INTO employees VALUES(217,'rfgerfger','','','','2026-10-05T15:35:12+00:00',NULL,1,3,1);
CREATE TABLE admins (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    job_title TEXT, 
    department_id INTEGER DEFAULT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
INSERT INTO admins VALUES(122,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(181,'',2);
INSERT INTO admins VALUES(216,'',NULL);
INSERT INTO admins VALUES(217,'',2);
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
INSERT INTO users VALUES(212,38);
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
INSERT INTO accounts VALUES(546,199,'userclient32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',0,'2026-09-15 14:20:02.897326+00:00');
INSERT INTO accounts VALUES(579,212,'client3user','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-10-01 21:23:18.757332+00:00');
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
INSERT INTO clients VALUES(32,181,'Клиент 1','','','1',1,26,'2026-09-08T14:13:04.962258','');
INSERT INTO clients VALUES(34,122,'Клиент даже не знаю как назвать','','','',1,4,'2026-09-09T12:45:02.670365','Не совсем обычный клиент');
INSERT INTO clients VALUES(36,122,'Клиент 2','','','Телефон',1,30,'2026-09-09T13:50:55.389754','Обычный клиент');
INSERT INTO clients VALUES(38,181,'Клиент 3','','','',1,3,'2026-10-01T18:22:15.734425+00:00','Плановые по средам');
INSERT INTO clients VALUES(39,181,'1111','','','',1,7,'2026-10-09T12:01:42.858551+00:00','');
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
INSERT INTO roles VALUES(71,'Может создавать заявки','ticket.operation,ticket.view','',0,'2026-10-01T15:50:38+00:00',0,0);
INSERT INTO roles VALUES(72,'string','client.operation','',0,'2026-10-05T12:09:19+00:00',1,0);
INSERT INTO roles VALUES(73,'Полные права','client.operation, client.view, client.decision, client.create, admin.operation, admin.view, department.operation, department.view, user.operation, user.view, ticket.operation, ticket.created, ticket.view, ticket.accepted, ticket.at_work, ticket.at_work_remote, ticket.at_work_retrospective, ticket.canceled, ticket.executed, role.assign, role_user.assign','Полные права',1,'2026-10-05T12:10:17+00:00',1,0);
INSERT INTO roles VALUES(74,'Старший менеджер','client.operation,client.view,role_user.assign,ticket.accepted,ticket.canceled,ticket.created,ticket.executed,ticket.operation,ticket.view,user.operation,user.view','Полные права',1,'2026-10-05T12:12:03+00:00',1,0);
INSERT INTO roles VALUES(75,'Менеджер','client.view,ticket.accepted,ticket.created,ticket.operation,ticket.view,user.view','Работа с заявками',1,'2026-10-05T12:13:36+00:00',1,0);
INSERT INTO roles VALUES(76,'Инженер с право удаленки','admin.view,client.view,ticket.at_work,ticket.at_work_remote,ticket.at_work_retrospective,ticket.created,ticket.operation,ticket.view,user.view','Инженер с правом удаленки',1,'2026-10-05T12:16:24+00:00',1,0);
INSERT INTO roles VALUES(77,'Инженер','admin.view,client.view,ticket.at_work,ticket.at_work_remote,ticket.at_work_retrospective,ticket.created,ticket.view,user.view','Инженер',1,'2026-10-05T12:16:45+00:00',1,0);
INSERT INTO roles VALUES(78,'string','client.view','efrf',0,'2026-10-09T15:07:29+00:00',1,0);
CREATE TABLE admins_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO admins_roles VALUES(181,73);
INSERT INTO admins_roles VALUES(122,73);
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
INSERT INTO user_tickets_status_record VALUES(34,199,1,'created','2026-10-01T15:52:19.558726+00:00','');
INSERT INTO user_tickets_status_record VALUES(35,181,1,'in_work','2026-10-01T15:52:19.559139+00:00','');
INSERT INTO user_tickets_status_record VALUES(36,199,2,'created','2026-10-01T16:07:03.114249+00:00','');
INSERT INTO user_tickets_status_record VALUES(37,181,2,'in_work','2026-10-01T16:07:03.115694+00:00','');
INSERT INTO user_tickets_status_record VALUES(38,181,1,'waiting_for_confirmation','2026-10-01T16:40:17.085686+00:00','');
INSERT INTO user_tickets_status_record VALUES(39,181,1,'confirmed_by_admin','2026-10-01T16:40:17.085977+00:00','');
INSERT INTO user_tickets_status_record VALUES(40,212,3,'created','2026-10-01T18:24:18.661275+00:00','');
INSERT INTO user_tickets_status_record VALUES(41,181,3,'in_work','2026-10-01T18:24:18.662287+00:00','');
INSERT INTO user_tickets_status_record VALUES(42,181,3,'waiting_for_confirmation','2026-10-01T18:25:57.361010+00:00','');
INSERT INTO user_tickets_status_record VALUES(43,181,3,'confirmed_by_admin','2026-10-01T18:25:57.361391+00:00','');
INSERT INTO user_tickets_status_record VALUES(44,210,4,'created','2026-10-02T11:15:08.000050+00:00','');
INSERT INTO user_tickets_status_record VALUES(45,181,4,'in_work','2026-10-02T11:15:08.000473+00:00','');
INSERT INTO user_tickets_status_record VALUES(46,210,5,'created','2026-10-05T14:25:45.476367+00:00','');
INSERT INTO user_tickets_status_record VALUES(47,181,5,'in_work','2026-10-05T14:25:45.479627+00:00','');
INSERT INTO user_tickets_status_record VALUES(48,181,5,'waiting_for_confirmation','2026-10-05T14:30:03.672020+00:00','');
INSERT INTO user_tickets_status_record VALUES(49,181,5,'confirmed_by_admin','2026-10-05T14:30:03.672118+00:00','');
INSERT INTO user_tickets_status_record VALUES(50,210,6,'created','2026-10-05T14:31:13.680548+00:00','');
INSERT INTO user_tickets_status_record VALUES(51,181,6,'in_work','2026-10-05T14:31:13.683360+00:00','');
INSERT INTO user_tickets_status_record VALUES(52,181,6,'waiting_for_confirmation','2026-10-05T14:32:07.034785+00:00','');
INSERT INTO user_tickets_status_record VALUES(53,181,6,'confirmed_by_admin','2026-10-05T14:32:07.034876+00:00','');
INSERT INTO user_tickets_status_record VALUES(54,199,7,'created','2026-10-05T14:34:11.035702+00:00','');
INSERT INTO user_tickets_status_record VALUES(55,181,7,'in_work','2026-10-05T14:34:11.036005+00:00','');
INSERT INTO user_tickets_status_record VALUES(56,181,2,'suspended','2026-10-05T14:34:39.016612+00:00','');
INSERT INTO user_tickets_status_record VALUES(57,181,7,'suspended','2026-10-05T14:34:39.016713+00:00','');
INSERT INTO user_tickets_status_record VALUES(58,181,7,'in_work','2026-10-05T14:34:55.269867+00:00','');
INSERT INTO user_tickets_status_record VALUES(59,181,7,'waiting_for_confirmation','2026-10-05T14:41:11.885978+00:00','');
INSERT INTO user_tickets_status_record VALUES(60,181,7,'confirmed_by_admin','2026-10-05T14:41:11.886096+00:00','');
INSERT INTO user_tickets_status_record VALUES(61,210,8,'created','2026-10-05T14:47:47.099638+00:00','');
INSERT INTO user_tickets_status_record VALUES(62,181,8,'in_work','2026-10-05T14:47:47.099943+00:00','');
INSERT INTO user_tickets_status_record VALUES(63,181,8,'waiting_for_confirmation','2026-10-05T14:49:33.790705+00:00','');
INSERT INTO user_tickets_status_record VALUES(64,181,8,'confirmed_by_admin','2026-10-05T14:49:33.790790+00:00','');
INSERT INTO user_tickets_status_record VALUES(65,210,9,'created','2026-10-05T14:58:25.751119+00:00','');
INSERT INTO user_tickets_status_record VALUES(66,181,9,'in_work','2026-10-05T14:58:25.751475+00:00','');
INSERT INTO user_tickets_status_record VALUES(67,210,10,'created','2026-10-05T15:15:47.622940+00:00','');
INSERT INTO user_tickets_status_record VALUES(68,181,10,'in_work','2026-10-05T15:15:47.623829+00:00','');
INSERT INTO user_tickets_status_record VALUES(69,181,10,'waiting_for_confirmation','2026-10-05T15:17:32.541875+00:00','');
INSERT INTO user_tickets_status_record VALUES(70,181,10,'confirmed_by_admin','2026-10-05T15:17:32.542142+00:00','');
INSERT INTO user_tickets_status_record VALUES(71,210,11,'created','2026-10-06T11:36:54.744983+00:00','');
INSERT INTO user_tickets_status_record VALUES(72,181,11,'in_work','2026-10-06T11:36:54.745917+00:00','');
INSERT INTO user_tickets_status_record VALUES(73,181,4,'suspended','2026-10-06T11:51:21.020586+00:00','');
INSERT INTO user_tickets_status_record VALUES(74,181,11,'suspended','2026-10-06T11:51:21.020726+00:00','');
INSERT INTO user_tickets_status_record VALUES(75,181,11,'in_work','2026-10-06T11:52:16.526973+00:00','');
INSERT INTO user_tickets_status_record VALUES(76,210,12,'created','2026-10-06T11:53:16.687481+00:00','');
INSERT INTO user_tickets_status_record VALUES(77,181,12,'in_work','2026-10-06T11:53:16.688577+00:00','');
INSERT INTO user_tickets_status_record VALUES(78,181,12,'suspended','2026-10-06T11:53:37.685266+00:00','');
INSERT INTO user_tickets_status_record VALUES(79,210,13,'created','2026-10-09T09:01:12.975938+00:00','');
INSERT INTO user_tickets_status_record VALUES(80,181,13,'in_work','2026-10-09T09:01:12.976771+00:00','');
INSERT INTO user_tickets_status_record VALUES(81,181,2,'suspended','2026-10-09T12:43:29.990928+00:00','');
INSERT INTO user_tickets_status_record VALUES(82,181,2,'suspended','2026-10-09T12:43:42.366194+00:00','');
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
INSERT INTO ticket_comments VALUES(11,9,181,'Принтер действительно не печатает','2026-10-01T15:53:48.423083+00:00');
INSERT INTO ticket_comments VALUES(12,14,181,'Как будто много полей лишних для заполнения','2026-10-02T15:02:00.306125+00:00');
INSERT INTO ticket_comments VALUES(13,17,181,'Принтер белый','2026-10-05T14:33:07.984563+00:00');
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
INSERT INTO user_tickets VALUES(1,32,199,199,'Не печатает принтер','2026-10-01T15:52:19.558726+00:00',2,'2026-10-01T16:40:17.085977+00:00','');
INSERT INTO user_tickets VALUES(2,32,199,199,'Обновить 1С','2026-10-01T16:07:03.114249+00:00',4,NULL,'');
INSERT INTO user_tickets VALUES(3,38,212,212,'Настроить','2026-10-01T18:24:18.661275+00:00',2,'2026-10-01T18:25:57.361391+00:00','');
INSERT INTO user_tickets VALUES(4,36,210,211,'Проверить','2026-10-02T11:15:08.000050+00:00',2,NULL,'');
INSERT INTO user_tickets VALUES(5,36,210,210,'Не печатает принтер','2026-10-05T14:25:45.476367+00:00',2,'2026-10-05T14:30:03.672118+00:00','');
INSERT INTO user_tickets VALUES(6,36,210,211,'Снова принтер','2026-10-05T14:31:13.680548+00:00',2,'2026-10-05T14:32:07.034876+00:00','');
INSERT INTO user_tickets VALUES(7,32,199,199,'Принтер','2026-10-05T14:34:11.035702+00:00',4,'2026-10-05T14:41:11.886096+00:00','Принтер');
INSERT INTO user_tickets VALUES(8,36,210,210,'капкупаукапкап','2026-10-05T14:47:47.099638+00:00',2,'2026-10-05T14:49:33.790790+00:00','');
INSERT INTO user_tickets VALUES(9,36,210,210,'jbg','2026-10-05T14:58:25.751119+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(10,36,210,210,'Сначала без отдела','2026-10-05T15:15:47.622940+00:00',2,'2026-10-05T15:17:32.542142+00:00','');
INSERT INTO user_tickets VALUES(11,36,210,210,'rheryjty','2026-10-06T11:36:54.744983+00:00',3,NULL,'');
INSERT INTO user_tickets VALUES(12,36,210,211,'dcwdcww','2026-10-06T11:53:16.687481+00:00',2,NULL,'');
INSERT INTO user_tickets VALUES(13,36,210,210,'rwrtrweergergerg','2026-10-09T09:01:12.975938+00:00',1,NULL,'');
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
INSERT INTO tickets VALUES(3,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-09-30T19:40:44.861466+00:00',0,'2026-10-01T12:00:00+00:00','normal',122,NULL,1);
INSERT INTO tickets VALUES(4,36,NULL,NULL,NULL,2,'string',NULL,'2026-09-30T19:41:59.381170+00:00',0,'2026-10-01T12:00:00+00:00','normal',0,'2026-10-01T16:44:30.772533+00:00',3);
INSERT INTO tickets VALUES(5,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T13:30:22.571755+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,'2026-10-01T14:16:45.787360+00:00',11);
INSERT INTO tickets VALUES(6,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-10-01T14:18:02.727712+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,'2026-10-01T14:21:52.567390+00:00',2);
INSERT INTO tickets VALUES(7,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:15.345594+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,NULL,3);
INSERT INTO tickets VALUES(8,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:35.006642+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(9,32,199,199,1,2,'Не печатает принтер',NULL,'2026-10-01T15:52:19.558984+00:00',1,NULL,'normal',0,'2026-10-01T16:40:17.085905+00:00',10);
INSERT INTO tickets VALUES(10,32,199,199,2,3,'Обновить 1С',NULL,'2026-10-01T16:07:03.115246+00:00',0,NULL,'maintenance',0,NULL,5);
INSERT INTO tickets VALUES(11,32,NULL,NULL,NULL,2,'Настроить что-нибудь',NULL,'2026-10-01T16:40:44.821067+00:00',1,NULL,'normal',0,NULL,5);
INSERT INTO tickets VALUES(12,38,212,212,3,2,'Настроить',NULL,'2026-10-01T18:24:18.661924+00:00',0,NULL,'normal',0,'2026-10-01T18:25:57.361332+00:00',3);
INSERT INTO tickets VALUES(13,36,210,211,4,2,'Проверить',NULL,'2026-10-02T11:15:08.000313+00:00',0,NULL,'normal',0,NULL,2);
INSERT INTO tickets VALUES(14,32,NULL,199,NULL,2,replace('Все плохо. Заявитель Маша 8900-90-60-90\n\nКак нового контакта добавить? и кто такой пользователь? Где проставлять исполнителя (инженера)?','\n',char(10)),'Чем описание отличается от текста заявки??? Где дата заявки?','2026-10-02T15:02:00.306125+00:00',0,'2026-10-05T14:58:00+00:00','normal',0,NULL,9);
INSERT INTO tickets VALUES(15,36,210,210,5,2,'Не печатает принтер',NULL,'2026-10-05T14:25:45.476588+00:00',0,NULL,'normal',0,'2026-10-05T14:30:03.672098+00:00',8);
INSERT INTO tickets VALUES(16,36,210,211,6,NULL,'Снова принтер',NULL,'2026-10-05T14:31:13.682328+00:00',0,NULL,'normal',0,'2026-10-05T14:32:07.034859+00:00',2);
INSERT INTO tickets VALUES(17,32,NULL,NULL,NULL,NULL,'Принтер',NULL,'2026-10-05T14:32:40.681634+00:00',0,NULL,'normal',0,'2026-10-05T14:33:49.254283+00:00',7);
INSERT INTO tickets VALUES(18,32,199,199,7,NULL,'Принтер','Принтер','2026-10-05T14:34:11.035894+00:00',0,NULL,'normal',0,'2026-10-05T14:41:11.886074+00:00',6);
INSERT INTO tickets VALUES(19,36,NULL,NULL,NULL,NULL,'какаукапукапук',NULL,'2026-10-05T14:46:00.588899+00:00',0,NULL,'normal',0,'2026-10-05T14:47:33.485372+00:00',4);
INSERT INTO tickets VALUES(20,36,210,210,8,NULL,'капкупаукапкап',NULL,'2026-10-05T14:47:47.099825+00:00',0,NULL,'normal',0,'2026-10-05T14:49:33.790774+00:00',3);
INSERT INTO tickets VALUES(21,36,NULL,210,NULL,NULL,'какапукапук',NULL,'2026-10-05T14:49:55.053814+00:00',0,NULL,'normal',0,'2026-10-05T14:57:21.394454+00:00',3);
INSERT INTO tickets VALUES(23,36,NULL,NULL,NULL,2,'Сначала отдел не назначен',NULL,'2026-10-05T15:11:28.715176+00:00',0,NULL,'normal',0,'2026-10-05T15:15:28.018442+00:00',4);
INSERT INTO tickets VALUES(24,36,210,210,10,2,'Сначала без отдела',NULL,'2026-10-05T15:15:47.623423+00:00',0,NULL,'normal',0,'2026-10-05T15:17:32.542078+00:00',4);
INSERT INTO tickets VALUES(25,36,NULL,NULL,NULL,2,'Теперь с отделом',NULL,'2026-10-05T15:18:04.551648+00:00',0,NULL,'normal',0,'2026-10-05T15:18:30.874723+00:00',3);
INSERT INTO tickets VALUES(26,36,NULL,NULL,NULL,2,'Без отдела',NULL,'2026-10-05T15:19:00.886365+00:00',0,NULL,'normal',0,'2026-10-05T15:19:28.833839+00:00',4);
INSERT INTO tickets VALUES(27,32,NULL,NULL,NULL,NULL,'ркеренорен',NULL,'2026-10-05T15:22:56.170880+00:00',0,NULL,'normal',0,'2026-10-05T15:28:11.574732+00:00',3);
INSERT INTO tickets VALUES(28,36,210,210,11,NULL,'rheryjty',NULL,'2026-10-06T11:36:54.745452+00:00',0,NULL,'normal',0,NULL,2);
INSERT INTO tickets VALUES(29,36,210,211,12,NULL,'dcwdcww',NULL,'2026-10-06T11:53:16.687858+00:00',0,NULL,'normal',0,NULL,1);
INSERT INTO tickets VALUES(30,36,210,210,13,NULL,'rwrtrweergergerg',NULL,'2026-10-09T09:01:12.976374+00:00',0,NULL,'normal',0,NULL,0);
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
INSERT INTO ticket_status_records VALUES(32,9,181,'created','2026-10-01T15:52:19.558984+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(33,9,181,'accepted','2026-10-01T15:52:19.559106+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(34,9,181,'deferred','2026-10-01T15:53:01.992218+00:00',NULL,NULL,NULL,NULL,'Позже',0);
INSERT INTO ticket_status_records VALUES(35,9,181,'assigned','2026-10-01T15:53:14.910656+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(36,9,181,'deferred','2026-10-01T15:54:19.319031+00:00',NULL,NULL,NULL,NULL,'Позже',0);
INSERT INTO ticket_status_records VALUES(37,9,181,'assigned','2026-10-01T15:54:38.600992+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(38,9,181,'assigned','2026-10-01T15:58:02.217903+00:00',122,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(39,7,181,'deferred','2026-10-01T15:58:38.910117+00:00',NULL,NULL,NULL,NULL,'Позже',0);
INSERT INTO ticket_status_records VALUES(40,10,181,'created','2026-10-01T16:07:03.115246+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(41,10,181,'accepted','2026-10-01T16:07:03.115581+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(42,10,181,'assigned','2026-10-01T16:07:20.246383+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(43,9,181,'accepted','2026-10-01T16:25:40.893642+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(44,3,181,'assigned','2026-10-01T16:27:13.462054+00:00',122,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(45,10,181,'deferred','2026-10-01T16:28:50.927235+00:00',NULL,NULL,NULL,NULL,'Отложено',0);
INSERT INTO ticket_status_records VALUES(46,9,181,'assigned','2026-10-01T16:39:41.948909+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(47,9,181,'at_work','2026-10-01T16:40:10.030911+00:00',NULL,NULL,NULL,1,'erfref',0);
INSERT INTO ticket_status_records VALUES(48,9,181,'ready_for_review','2026-10-01T16:40:17.085589+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(49,9,181,'executed','2026-10-01T16:40:17.085905+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(50,11,181,'created','2026-10-01T16:40:44.821067+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(51,11,181,'accepted','2026-10-01T16:40:44.821332+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(52,4,181,'assigned','2026-10-01T16:44:24.715214+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(53,4,181,'at_work','2026-10-01T16:44:30.772428+00:00',NULL,NULL,NULL,0,'',3600);
INSERT INTO ticket_status_records VALUES(54,4,181,'ready_for_review','2026-10-01T16:44:30.772428+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(55,4,181,'executed','2026-10-01T16:44:30.772533+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(56,12,181,'created','2026-10-01T18:24:18.661924+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(57,12,181,'accepted','2026-10-01T18:24:18.662220+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(58,12,181,'assigned','2026-10-01T18:24:30.431045+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(59,12,181,'assigned','2026-10-01T18:24:55.269481+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(60,12,181,'at_work','2026-10-01T18:25:57.360897+00:00',NULL,NULL,NULL,0,'',3600);
INSERT INTO ticket_status_records VALUES(61,12,181,'ready_for_review','2026-10-01T18:25:57.360897+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(62,12,181,'executed','2026-10-01T18:25:57.361332+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(63,11,181,'assigned','2026-10-01T18:33:11.688544+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(64,11,181,'assigned','2026-10-01T18:39:58.035296+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(65,13,181,'created','2026-10-02T11:15:08.000313+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(66,13,181,'accepted','2026-10-02T11:15:08.000442+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(67,13,181,'assigned','2026-10-02T11:15:26.276756+00:00',181,NULL,NULL,NULL,'Назначить',0);
INSERT INTO ticket_status_records VALUES(68,14,181,'created','2026-10-02T15:02:00.306125+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(69,14,181,'accepted','2026-10-02T15:02:00.306238+00:00',NULL,NULL,NULL,NULL,'Как будто много полей лишних для заполнения',0);
INSERT INTO ticket_status_records VALUES(70,14,181,'assigned','2026-10-05T11:45:43.925576+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(71,14,181,'accepted','2026-10-05T11:46:12.389806+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(72,14,181,'assigned','2026-10-05T11:47:59.752593+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(73,15,181,'created','2026-10-05T14:25:45.476588+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(74,15,181,'accepted','2026-10-05T14:25:45.479582+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(75,15,181,'assigned','2026-10-05T14:26:51.507240+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(76,15,181,'accepted','2026-10-05T14:27:53.744348+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(77,15,181,'assigned','2026-10-05T14:28:46.751457+00:00',217,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(78,15,181,'assigned','2026-10-05T14:29:20.480969+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(79,15,181,'at_work','2026-10-05T14:29:36.864848+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(80,15,181,'paused','2026-10-05T14:29:44.525458+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(81,15,181,'at_work','2026-10-05T14:29:57.693144+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(82,15,181,'ready_for_review','2026-10-05T14:30:03.671992+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(83,15,181,'executed','2026-10-05T14:30:03.672098+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(84,16,181,'created','2026-10-05T14:31:13.682328+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(85,16,181,'accepted','2026-10-05T14:31:13.683312+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(86,16,181,'assigned','2026-10-05T14:31:18.516998+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(87,16,181,'at_work','2026-10-05T14:32:07.034744+00:00',NULL,NULL,NULL,0,'',7200);
INSERT INTO ticket_status_records VALUES(88,16,181,'ready_for_review','2026-10-05T14:32:07.034744+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(89,16,181,'executed','2026-10-05T14:32:07.034859+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(90,17,181,'created','2026-10-05T14:32:40.681634+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(91,17,181,'accepted','2026-10-05T14:32:40.681743+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(92,17,181,'assigned','2026-10-05T14:32:49.508747+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(93,17,181,'assigned','2026-10-05T14:33:18.185483+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(94,17,181,'at_work','2026-10-05T14:33:23.992622+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(95,17,181,'paused','2026-10-05T14:33:25.775519+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(96,17,181,'at_work','2026-10-05T14:33:35.576541+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(97,17,181,'ready_for_review','2026-10-05T14:33:49.254206+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(98,17,181,'executed','2026-10-05T14:33:49.254283+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(99,18,181,'created','2026-10-05T14:34:11.035894+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(100,18,181,'accepted','2026-10-05T14:34:11.035985+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(101,18,181,'assigned','2026-10-05T14:34:14.586293+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(102,10,181,'suspended','2026-10-05T14:34:39.016590+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(103,11,181,'suspended','2026-10-05T14:34:39.016622+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(104,14,181,'suspended','2026-10-05T14:34:39.016630+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(105,18,181,'suspended','2026-10-05T14:34:39.016636+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(106,18,181,'accepted','2026-10-05T14:34:55.269845+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(107,18,181,'assigned','2026-10-05T14:41:06.818660+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(108,18,181,'at_work','2026-10-05T14:41:09.790222+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(109,18,181,'ready_for_review','2026-10-05T14:41:11.885948+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(110,18,181,'executed','2026-10-05T14:41:11.886074+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(111,19,181,'created','2026-10-05T14:46:00.588899+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(112,19,181,'accepted','2026-10-05T14:46:00.589052+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(113,19,181,'assigned','2026-10-05T14:47:24.391081+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(114,19,181,'at_work','2026-10-05T14:47:30.937013+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(115,19,181,'ready_for_review','2026-10-05T14:47:33.485312+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(116,19,181,'executed','2026-10-05T14:47:33.485372+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(117,20,181,'created','2026-10-05T14:47:47.099825+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(118,20,181,'accepted','2026-10-05T14:47:47.099920+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(119,20,181,'assigned','2026-10-05T14:47:55.168662+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(120,20,181,'at_work','2026-10-05T14:49:02.601768+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(121,14,181,'accepted','2026-10-05T14:49:18.704241+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(122,20,181,'ready_for_review','2026-10-05T14:49:33.790681+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(123,20,181,'executed','2026-10-05T14:49:33.790774+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(124,21,181,'created','2026-10-05T14:49:55.053814+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(125,21,181,'accepted','2026-10-05T14:49:55.053913+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(126,21,181,'assigned','2026-10-05T14:49:58.342010+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(127,21,181,'at_work','2026-10-05T14:50:00.555768+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(128,21,181,'ready_for_review','2026-10-05T14:57:21.394379+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(129,21,181,'executed','2026-10-05T14:57:21.394454+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(130,22,181,'created','2026-10-05T14:58:25.751340+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(131,22,181,'accepted','2026-10-05T14:58:25.751448+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(132,22,181,'assigned','2026-10-05T14:58:44.357884+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(133,22,181,'assigned','2026-10-05T14:59:09.995155+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(134,22,181,'assigned','2026-10-05T15:00:12.181021+00:00',217,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(135,22,181,'assigned','2026-10-05T15:00:22.597439+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(136,23,181,'created','2026-10-05T15:11:28.715176+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(137,23,181,'accepted','2026-10-05T15:11:28.715499+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(138,23,181,'assigned','2026-10-05T15:12:15.648101+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(139,23,181,'at_work','2026-10-05T15:15:21.263800+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(140,23,181,'ready_for_review','2026-10-05T15:15:28.018232+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(141,23,181,'executed','2026-10-05T15:15:28.018442+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(142,24,181,'created','2026-10-05T15:15:47.623423+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(143,24,181,'accepted','2026-10-05T15:15:47.623733+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(144,24,181,'assigned','2026-10-05T15:16:01.438156+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(145,24,181,'at_work','2026-10-05T15:16:14.406499+00:00',NULL,NULL,NULL,0,'Начать работу',0);
INSERT INTO ticket_status_records VALUES(146,24,181,'ready_for_review','2026-10-05T15:17:32.541780+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(147,24,181,'executed','2026-10-05T15:17:32.542078+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(148,25,181,'created','2026-10-05T15:18:04.551648+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(149,25,181,'accepted','2026-10-05T15:18:04.551947+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(150,25,181,'assigned','2026-10-05T15:18:10.505070+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(151,25,181,'at_work','2026-10-05T15:18:25.112659+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(152,25,181,'ready_for_review','2026-10-05T15:18:30.874523+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(153,25,181,'executed','2026-10-05T15:18:30.874723+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(154,26,181,'created','2026-10-05T15:19:00.886365+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(155,26,181,'accepted','2026-10-05T15:19:00.886647+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(156,26,181,'assigned','2026-10-05T15:19:12.989545+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(157,26,181,'at_work','2026-10-05T15:19:24.463084+00:00',NULL,NULL,NULL,0,'Начали работу',0);
INSERT INTO ticket_status_records VALUES(158,26,181,'ready_for_review','2026-10-05T15:19:28.833640+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(159,26,181,'executed','2026-10-05T15:19:28.833839+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(160,27,181,'created','2026-10-05T15:22:56.170880+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(161,27,181,'accepted','2026-10-05T15:22:56.171169+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(162,14,181,'suspended','2026-10-05T15:23:05.952003+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(163,27,181,'suspended','2026-10-05T15:23:05.952047+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(164,27,181,'accepted','2026-10-05T15:27:42.485530+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(165,27,181,'cancelled','2026-10-05T15:28:11.574732+00:00',NULL,NULL,NULL,NULL,'efefrefer',0);
INSERT INTO ticket_status_records VALUES(166,28,181,'created','2026-10-06T11:36:54.745452+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(167,28,181,'accepted','2026-10-06T11:36:54.745821+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(168,13,181,'suspended','2026-10-06T11:51:21.020475+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(169,28,181,'suspended','2026-10-06T11:51:21.020660+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(170,28,181,'accepted','2026-10-06T11:52:16.526884+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(171,29,181,'created','2026-10-06T11:53:16.687858+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(172,29,181,'accepted','2026-10-06T11:53:16.688504+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(173,29,181,'suspended','2026-10-06T11:53:37.685194+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(174,30,181,'created','2026-10-09T09:01:12.976374+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(175,30,181,'accepted','2026-10-09T09:01:12.976689+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(176,10,181,'suspended','2026-10-09T12:43:29.990812+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(177,11,181,'suspended','2026-10-09T12:43:29.990853+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(178,14,181,'suspended','2026-10-09T12:43:29.990886+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(179,10,181,'suspended','2026-10-09T12:43:42.366084+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(180,11,181,'suspended','2026-10-09T12:43:42.366125+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(181,14,181,'suspended','2026-10-09T12:43:42.366158+00:00',NULL,NULL,NULL,NULL,'',0);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',217);
INSERT INTO sqlite_sequence VALUES('accounts',589);
INSERT INTO sqlite_sequence VALUES('roles',79);
INSERT INTO sqlite_sequence VALUES('clients',39);
INSERT INTO sqlite_sequence VALUES('user_tickets_status_record',82);
INSERT INTO sqlite_sequence VALUES('user_tickets_comment',3);
INSERT INTO sqlite_sequence VALUES('departments',9);
INSERT INTO sqlite_sequence VALUES('ticket_comments',13);
INSERT INTO sqlite_sequence VALUES('tickets',30);
INSERT INTO sqlite_sequence VALUES('ticket_status_records',181);
INSERT INTO sqlite_sequence VALUES('user_tickets',13);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
CREATE UNIQUE INDEX idx_departments_name
ON departments(name);
CREATE INDEX idx_ticket_comments_ticket_id
ON ticket_comments(ticket_id, ticket_comment_id);
CREATE INDEX idx_ticket_comments_employee_id
ON ticket_comments(employee_id);
COMMIT;

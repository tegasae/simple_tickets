PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE departments (
    department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 0,
    date_created TEXT
);
INSERT INTO departments VALUES(2,'Суппорт',1,42,'2026-07-27T16:02:50.257132');
INSERT INTO departments VALUES(3,'1С',1,9,'2026-07-27T16:03:05.569976');
INSERT INTO departments VALUES(5,'Веб',1,6,'2026-09-07T17:04:25.825200');
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
	version INTEGER NOT NULL DEFAULT 0,
	is_admin INTEGER);
INSERT INTO employees VALUES(122,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19 13:29:27+00:00',NULL,1,12,1);
INSERT INTO employees VALUES(181,'Тэга','','','','2026-09-08T14:11:07+00:00',NULL,1,19,1);
INSERT INTO employees VALUES(184,'Роман','Новичихин','','','2026-09-09 12:45:17.526999+00:00',NULL,0,5,0);
INSERT INTO employees VALUES(199,'Пользователь 1','','','','2026-09-15 14:20:02.897155+00:00',NULL,0,19,0);
INSERT INTO employees VALUES(200,'Пользователь 2','','','','2026-09-15 15:29:01.063413+00:00',NULL,1,11,0);
INSERT INTO employees VALUES(210,'Пользователь 1 клиента 2','','','','2026-10-01 18:41:33.728954+00:00',NULL,1,16,0);
INSERT INTO employees VALUES(211,'Пользователь 2 Клиента 2','','','','2026-10-01 18:41:54.906240+00:00',NULL,0,5,0);
INSERT INTO employees VALUES(212,'Пользователь клиента 3','','','','2026-10-01 21:22:37.069747+00:00',NULL,1,2,0);
INSERT INTO employees VALUES(216,'efwef','','','','2026-10-05T15:27:46+00:00',NULL,1,1,1);
INSERT INTO employees VALUES(217,'rfgerfger','','','','2026-10-05T15:35:12+00:00',NULL,1,3,1);
INSERT INTO employees VALUES(218,'vfvefv','erfgerf','','erer','2026-10-26 20:48:51.050411+00:00',NULL,1,8,0);
INSERT INTO employees VALUES(219,'string','','','','2026-10-26 20:50:04.448261+00:00',NULL,1,0,1);
INSERT INTO employees VALUES(220,'Обычный пользователь','','','','2026-11-20 19:14:51.730199+00:00',NULL,1,3,1);
INSERT INTO employees VALUES(221,'Обычный инженер','','','','2026-11-20 19:37:57.089254+00:00',NULL,1,8,1);
INSERT INTO employees VALUES(222,'Опытный инженер','','','','2026-11-20 19:40:21.912237+00:00',NULL,1,4,1);
INSERT INTO employees VALUES(223,'Обычный инженер с работой на удаленке','','','','2026-11-20 19:43:49.300517+00:00',NULL,1,17,1);
INSERT INTO employees VALUES(224,'Менеджер','','','','2026-11-20 19:45:17.195260+00:00',NULL,1,5,1);
INSERT INTO employees VALUES(225,'Руководитель отдела','','','','2026-11-20 19:47:26.660021+00:00',NULL,1,1,1);
INSERT INTO employees VALUES(226,'Обычный пользователь клиента','','','','2026-11-20 19:53:56.816347+00:00',NULL,1,10,0);
INSERT INTO employees VALUES(227,'Главный пользователь клиента','','','','2026-11-20 19:54:58.990940+00:00',NULL,1,7,0);
INSERT INTO employees VALUES(228,'Web программист','','','','2026-11-22 15:22:24.543087+00:00',NULL,1,2,1);
INSERT INTO employees VALUES(229,'Web программист еще один','','','','2026-11-22 15:25:33.275840+00:00',NULL,1,1,1);
INSERT INTO employees VALUES(230,'Еще один инженер','','','','2026-11-23 14:53:22.450012+00:00',NULL,1,1,1);
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
INSERT INTO admins VALUES(219,'',NULL);
INSERT INTO admins VALUES(220,'',NULL);
INSERT INTO admins VALUES(221,'',2);
INSERT INTO admins VALUES(222,'',2);
INSERT INTO admins VALUES(223,'',2);
INSERT INTO admins VALUES(224,'',NULL);
INSERT INTO admins VALUES(225,'',NULL);
INSERT INTO admins VALUES(228,'',5);
INSERT INTO admins VALUES(229,'',5);
INSERT INTO admins VALUES(230,'',2);
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
INSERT INTO users VALUES(218,32);
INSERT INTO users VALUES(226,40);
INSERT INTO users VALUES(227,40);
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	login TEXT,
	password TEXT,
	enabled INTEGER DEFAULT (1),
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO accounts VALUES(406,122,'alice.johnson20260519132927','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-05-19T13:29:27');
INSERT INTO accounts VALUES(525,181,'tega','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-09-08T14:11:07');
INSERT INTO accounts VALUES(546,199,'userclient32','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',0,'2026-09-15 14:20:02.897326+00:00');
INSERT INTO accounts VALUES(579,212,'client3user','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-10-01 21:23:18.757332+00:00');
INSERT INTO accounts VALUES(590,218,'login32','30b85fc0a0bdf0793b4e0485712cba9bacd5027649ec7d497b082e4b6fcd155d',1,'2026-10-26 20:48:51.050602+00:00');
INSERT INTO accounts VALUES(597,220,'standard_user','03c50b40481cccc7e410067bdc39ae2d27c59f410ad4d27d1860e502a2dd565c',1,'2026-11-20 19:17:29.097181+00:00');
INSERT INTO accounts VALUES(600,221,'standard_engineer','e8c80bdfa5e863b115feb10c8dd1950b8ba38f40528587c4c80544738461345c',1,'2026-11-20 19:39:04.226083+00:00');
INSERT INTO accounts VALUES(601,222,'chief_engineer','0654dfb8fa7e2762852602d19e65c1b8803c5b411b60f3c78be7ac725e65c531',1,'2026-11-20 19:40:21.912262+00:00');
INSERT INTO accounts VALUES(604,223,'remote_engineer','0823f3e0eeefeb44b8b44fcd4be8746b062d4c4164ef90d1f119da8caa059288',1,'2026-11-20 19:43:49.300552+00:00');
INSERT INTO accounts VALUES(606,224,'manager','fbd4b3f3869b7bcf8b416d4ff701b4d97ac5b76792cb29000a674b74de9112a3',1,'2026-11-20 19:45:17.195286+00:00');
INSERT INTO accounts VALUES(608,225,'chief_department','c0addc6e456ed0093c70a300396c9e5daacaf5e9680f138a4d156473f7e841a7',1,'2026-11-20 19:47:26.660043+00:00');
INSERT INTO accounts VALUES(611,226,'standard_client_user','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-11-20 19:53:56.816376+00:00');
INSERT INTO accounts VALUES(613,227,'chief_client_user','9fa0fc85458256170f9918256a64cf3895826ef26bb05cccf9edb45eaaece4f8',1,'2026-11-20 19:54:58.990984+00:00');
INSERT INTO accounts VALUES(615,228,'web_user','19b53e8fdb5be184996683c27506f6dc0fbd087056844c093ddf2f1c814f592f',1,'2026-11-22 15:22:24.543661+00:00');
INSERT INTO accounts VALUES(617,229,'web_user_another','2fadf54d493cb6367599a20d39e6527afcec927c277b84f6523632174724ad4a',1,'2026-11-22 15:25:33.275974+00:00');
INSERT INTO accounts VALUES(625,230,'another_engineer','pbkdf2_sha256_v1$70b95babc75bb3565c4f9c739b1e93e5$455b1bbea048e335515226ddccd50d04752a565f68c9ba5d1e44820d4b9becee',1,'2026-11-23 14:53:22.818765+00:00');
CREATE TABLE clients (
	client_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	name TEXT,
	address TEXT,
	email TEXT,
	phone TEXT,
	enabled INTEGER, version INTEGER NOT NULL DEFAULT 0,
	date_created TEXT, description TEXT DEFAULT (''),
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO clients VALUES(32,181,'Клиент 1','','','1',1,41,'2026-09-08T14:13:04.962258','');
INSERT INTO clients VALUES(34,122,'Клиент даже не знаю как назвать','','','',1,4,'2026-09-09T12:45:02.670365','Не совсем обычный клиент');
INSERT INTO clients VALUES(36,122,'Клиент 2','','','Телефон',1,31,'2026-09-09T13:50:55.389754','Обычный клиент');
INSERT INTO clients VALUES(38,181,'Клиент 3','','','',1,3,'2026-10-01T18:22:15.734425+00:00','Плановые по средам');
INSERT INTO clients VALUES(39,181,'1111','','','',1,7,'2026-10-09T12:01:42.858551+00:00','');
INSERT INTO clients VALUES(40,181,'Клиент для заявок','','','',1,22,'2026-11-20T16:49:57.811433+00:00','');
INSERT INTO clients VALUES(41,224,'Новый клиент','','','',1,1,'2026-11-23T10:05:00.668726+00:00','');
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT NOT NULL,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER DEFAULT 0);
INSERT INTO roles VALUES(5,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.created, ticket.view, ticket.accepted, ticket.at_work, ticket.at_work_remote, ticket.at_work_retrospective, ticket.canceled, ticket.executed, role.assign, role_user.assign','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(60,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.created, ticket.view, ticket.accepted, ticket.at_work, ticket.at_work_remote, ticket.at_work_retrospective, ticket.canceled, ticket.executed, role.assign, role_user.assign','Full system access','-','2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(61,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:21:42+00:00',0,0);
INSERT INTO roles VALUES(62,'Super Admin','role.assign,admin.view','Full system access',0,'2026-03-23T12:22:06+00:00',1,0);
INSERT INTO roles VALUES(63,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:22:06+00:00',0,0);
INSERT INTO roles VALUES(64,'Super Admin','role.assign,admin.view','Full system access',0,'2026-03-23T12:22:34+00:00',1,0);
INSERT INTO roles VALUES(66,'Super Admin','role.assign,admin.view','Full system access',0,'2026-03-23T12:22:49+00:00',1,0);
INSERT INTO roles VALUES(67,'Can accepted','ticket.accepted','ticket.accepted',0,'2026-03-23T12:22:49+00:00',1,NULL);
INSERT INTO roles VALUES(71,'Может создавать заявки','ticket.operation,ticket.view','',0,'2026-10-01T15:50:38+00:00',0,0);
INSERT INTO roles VALUES(72,'string','client.operation','',0,'2026-10-05T12:09:19+00:00',1,0);
INSERT INTO roles VALUES(73,'Полные права','client.operation,client.view, client.decision,client.create,admin.operation,admin.view,department.operation,department.view,user.operation,user.view,ticket.operation,ticket.created,ticket.view,ticket.accepted,ticket.at_work,ticket.at_work_remote,ticket.assign_executor,ticket.set_remote_recommendation,ticket.at_work_retrospective,ticket.canceled,ticket.delete,ticket.executed,role.assign,role_user.assign','Полные права',0,'2026-10-05T12:10:17+00:00',1,0);
INSERT INTO roles VALUES(74,'Старший менеджер','client.operation,client.view,role_user.assign,ticket.accepted,ticket.canceled,ticket.created,ticket.executed,ticket.operation,ticket.view,user.operation,user.view','Полные права',0,'2026-10-05T12:12:03+00:00',1,0);
INSERT INTO roles VALUES(75,'Менеджер','client.view,ticket.accepted,ticket.created,ticket.operation,ticket.view,user.view','Работа с заявками',0,'2026-10-05T12:13:36+00:00',1,0);
INSERT INTO roles VALUES(76,'Инженер с право удаленки','admin.view,client.view,ticket.at_work,ticket.at_work_remote,ticket.at_work_retrospective,ticket.created,ticket.operation,ticket.view,user.view','Инженер с правом удаленки',0,'2026-10-05T12:16:24+00:00',1,0);
INSERT INTO roles VALUES(77,'Инженер','admin.view,client.view,ticket.at_work,ticket.at_work_remote,ticket.at_work_retrospective,ticket.created,ticket.view,user.view','Инженер',0,'2026-10-05T12:16:45+00:00',1,0);
INSERT INTO roles VALUES(78,'string','client.view','efrf',0,'2026-10-09T15:07:29+00:00',1,0);
INSERT INTO roles VALUES(80,'Обычный пользователь','admin.view,client.view,department.view,ticket.created,ticket.view, user.view','Базовая роль, все остальные основаны на ней',0,'2026-11-19 13:14:10.653809+00:00',1,0);
INSERT INTO roles VALUES(81,'Обычный инженер','ticket.at_work,ticket.at_work_retrospective,ticket.created,ticket.view','Обычный инженер, может выполнять заявки, основывается на базовой роли',0,'2026-11-19 13:18:04.438066+00:00',1,0);
INSERT INTO roles VALUES(82,'Опытный инженер','ticket.accepted,ticket.executed','Опытный инженер, может подтверждать заявки и подтверждать выполнение, основывается на роли обычного инженера',0,'2026-11-19 13:21:06.478717+00:00',1,0);
INSERT INTO roles VALUES(83,'Удаленщик','ticket.at_work_remote','Работа на горячей линии, добавляется к ролям инженеров',0,'2026-11-19 13:38:31.616620+00:00',1,0);
INSERT INTO roles VALUES(84,'Менеджер','client.create,client.decision,client.operation,ticket.accepted,ticket.canceled,ticket.executed,ticket.operation,user.operation,ticket.set_remote_recommendation','Роль менеджера, базируется на роли обычного пользователя',0,'2026-11-19 13:44:04.617319+00:00',1,0);
INSERT INTO roles VALUES(85,'Управление админстраторами','admin.operation,department.operation,department.view,role.assign,role_user.assign','Роль управления админстраторами, базируется на роли обычного пользователя',0,'2026-11-19 13:46:58.249169+00:00',1,0);
INSERT INTO roles VALUES(86,'Обычный пользователь','ticket.operation,ticket.view','Обычный пользователь клиент',0,'2026-11-20 14:31:14.307413+00:00',0,0);
INSERT INTO roles VALUES(87,'Обычный пользователь','ticket.operation,ticket.view','Обычный пользователь клиент',0,'2026-11-20 14:34:14.734658+00:00',0,0);
INSERT INTO roles VALUES(88,'Главный пользователь','ticket.operation.all,ticket.view.all','Роль главного пользователя клиента, добавляется к роли обычного пользователя',0,'2026-11-20 14:39:07.513313+00:00',0,0);
CREATE TABLE admins_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO admins_roles VALUES(122,73);
INSERT INTO admins_roles VALUES(181,73);
INSERT INTO admins_roles VALUES(220,80);
INSERT INTO admins_roles VALUES(221,80);
INSERT INTO admins_roles VALUES(221,81);
INSERT INTO admins_roles VALUES(222,80);
INSERT INTO admins_roles VALUES(222,81);
INSERT INTO admins_roles VALUES(222,82);
INSERT INTO admins_roles VALUES(223,80);
INSERT INTO admins_roles VALUES(223,81);
INSERT INTO admins_roles VALUES(223,83);
INSERT INTO admins_roles VALUES(224,80);
INSERT INTO admins_roles VALUES(224,84);
INSERT INTO admins_roles VALUES(225,80);
INSERT INTO admins_roles VALUES(225,84);
INSERT INTO admins_roles VALUES(225,85);
INSERT INTO admins_roles VALUES(228,80);
INSERT INTO admins_roles VALUES(228,81);
INSERT INTO admins_roles VALUES(229,80);
INSERT INTO admins_roles VALUES(229,81);
INSERT INTO admins_roles VALUES(230,80);
INSERT INTO admins_roles VALUES(230,81);
INSERT INTO admins_roles VALUES(230,83);
CREATE TABLE users_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO users_roles VALUES(199,61);
INSERT INTO users_roles VALUES(210,61);
INSERT INTO users_roles VALUES(210,63);
INSERT INTO users_roles VALUES(211,61);
INSERT INTO users_roles VALUES(211,63);
INSERT INTO users_roles VALUES(218,61);
INSERT INTO users_roles VALUES(226,87);
INSERT INTO users_roles VALUES(227,87);
INSERT INTO users_roles VALUES(227,88);
CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
INSERT INTO user_tickets_comment VALUES(4,24,226,'Комментарий','2026-11-23T10:46:29.894605+00:00');
INSERT INTO user_tickets_comment VALUES(5,25,226,'Комментарий','2026-11-23T11:44:03.560514+00:00');
INSERT INTO user_tickets_comment VALUES(6,26,226,'1111','2026-11-24T12:15:13.453035+00:00');
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
INSERT INTO user_tickets_status_record VALUES(76,210,12,'created','2026-10-06T11:53:16.687481+00:00','');
INSERT INTO user_tickets_status_record VALUES(77,181,12,'in_work','2026-10-06T11:53:16.688577+00:00','');
INSERT INTO user_tickets_status_record VALUES(78,181,12,'suspended','2026-10-06T11:53:37.685266+00:00','');
INSERT INTO user_tickets_status_record VALUES(79,210,13,'created','2026-10-09T09:01:12.975938+00:00','');
INSERT INTO user_tickets_status_record VALUES(80,181,13,'in_work','2026-10-09T09:01:12.976771+00:00','');
INSERT INTO user_tickets_status_record VALUES(83,218,14,'created','2026-11-18T13:51:53.937916+00:00','');
INSERT INTO user_tickets_status_record VALUES(84,181,14,'in_work','2026-11-18T13:51:53.942084+00:00','');
INSERT INTO user_tickets_status_record VALUES(85,218,15,'created','2026-11-18T14:19:28.830936+00:00','');
INSERT INTO user_tickets_status_record VALUES(86,181,15,'in_work','2026-11-18T14:19:28.831907+00:00','');
INSERT INTO user_tickets_status_record VALUES(91,218,18,'created','2026-11-18T15:15:53.038774+00:00','');
INSERT INTO user_tickets_status_record VALUES(92,181,18,'in_work','2026-11-18T15:15:53.041094+00:00','');
INSERT INTO user_tickets_status_record VALUES(93,181,18,'waiting_for_confirmation','2026-11-18T15:35:35.061248+00:00','');
INSERT INTO user_tickets_status_record VALUES(94,181,18,'in_work','2026-11-18T15:36:36.593703+00:00','');
INSERT INTO user_tickets_status_record VALUES(95,226,19,'created','2026-11-22T12:46:09.703393+00:00','');
INSERT INTO user_tickets_status_record VALUES(96,222,19,'in_work','2026-11-22T12:46:14.070439+00:00','');
INSERT INTO user_tickets_status_record VALUES(97,226,20,'created','2026-11-22T17:06:02.665139+00:00','');
INSERT INTO user_tickets_status_record VALUES(98,226,21,'created','2026-11-22T17:09:18.210078+00:00','');
INSERT INTO user_tickets_status_record VALUES(99,224,21,'in_work','2026-11-22T17:14:58.826561+00:00','');
INSERT INTO user_tickets_status_record VALUES(100,223,21,'waiting_for_confirmation','2026-11-22T17:21:40.275445+00:00','');
INSERT INTO user_tickets_status_record VALUES(101,226,21,'confirmed_by_user','2026-11-22T17:26:21.326405+00:00','');
INSERT INTO user_tickets_status_record VALUES(102,227,20,'cancelled_by_user','2026-11-22T17:37:33.927695+00:00','');
INSERT INTO user_tickets_status_record VALUES(103,223,19,'waiting_for_confirmation','2026-11-22T17:45:59.932497+00:00','');
INSERT INTO user_tickets_status_record VALUES(104,224,19,'confirmed_by_admin','2026-11-22T17:47:10.082114+00:00','');
INSERT INTO user_tickets_status_record VALUES(105,227,22,'created','2026-11-22T17:50:53.731051+00:00','');
INSERT INTO user_tickets_status_record VALUES(106,227,23,'created','2026-11-22T17:51:37.140197+00:00','');
INSERT INTO user_tickets_status_record VALUES(107,224,22,'cancelled_by_admin','2026-11-22T17:53:34.628188+00:00','Отказали');
INSERT INTO user_tickets_status_record VALUES(108,224,23,'suspended','2026-11-22T17:55:37.415361+00:00','');
INSERT INTO user_tickets_status_record VALUES(109,226,24,'created','2026-11-23T10:46:29.894605+00:00','');
INSERT INTO user_tickets_status_record VALUES(110,224,24,'in_work','2026-11-23T10:46:29.895448+00:00','Комментарий');
INSERT INTO user_tickets_status_record VALUES(111,226,25,'created','2026-11-23T11:44:03.560514+00:00','');
INSERT INTO user_tickets_status_record VALUES(112,224,25,'in_work','2026-11-23T11:44:03.561247+00:00','Комментарий');
INSERT INTO user_tickets_status_record VALUES(113,226,26,'created','2026-11-24T12:15:13.453035+00:00','');
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
INSERT INTO ticket_comments VALUES(5,12,122,'На следующие выезд захватить бизнес-тренера','2026-09-09T09:51:27.190503+00:00');
INSERT INTO ticket_comments VALUES(6,15,122,'comment1','2026-09-15T15:31:58.910575+00:00');
INSERT INTO ticket_comments VALUES(7,16,122,'jm uil;.','2026-09-16T09:48:49.833694+00:00');
INSERT INTO ticket_comments VALUES(8,3,181,'fergferg','2026-09-30T19:40:44.861466+00:00');
INSERT INTO ticket_comments VALUES(9,4,181,'fergferg','2026-09-30T19:41:59.381170+00:00');
INSERT INTO ticket_comments VALUES(10,5,181,'укукака','2026-10-01T13:31:42.525384+00:00');
INSERT INTO ticket_comments VALUES(11,9,181,'Принтер действительно не печатает','2026-10-01T15:53:48.423083+00:00');
INSERT INTO ticket_comments VALUES(12,14,181,'Как будто много полей лишних для заполнения','2026-10-02T15:02:00.306125+00:00');
INSERT INTO ticket_comments VALUES(13,17,181,'Принтер белый','2026-10-05T14:33:07.984563+00:00');
INSERT INTO ticket_comments VALUES(14,40,181,'ewfrwferfgergfergerg','2026-11-18T15:38:16.775121+00:00');
INSERT INTO ticket_comments VALUES(15,41,222,'Комментарий','2026-11-21T08:13:03.516555+00:00');
INSERT INTO ticket_comments VALUES(16,53,224,'Комментарий','2026-11-23T10:46:29.894998+00:00');
INSERT INTO ticket_comments VALUES(17,54,224,'Комментарий','2026-11-23T11:44:03.560853+00:00');
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
INSERT INTO user_tickets VALUES(14,32,218,218,'string','2026-11-18T13:51:53.937916+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(15,32,218,200,'string','2026-11-18T14:19:28.830936+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(18,32,218,200,'string','2026-11-18T15:15:53.038774+00:00',6,NULL,'');
INSERT INTO user_tickets VALUES(19,40,226,226,'Нам позвонил пользователь клиента','2026-11-22T12:46:09.703393+00:00',4,'2026-11-22T17:47:10.082114+00:00','');
INSERT INTO user_tickets VALUES(20,40,226,226,'Пользователь клиента делает заявку','2026-11-22T17:06:02.665139+00:00',1,'2026-11-22T17:37:33.927695+00:00','');
INSERT INTO user_tickets VALUES(21,40,226,226,'Пользователь клиента делает заявку еще раз','2026-11-22T17:09:18.210078+00:00',5,'2026-11-22T17:26:21.326405+00:00','');
INSERT INTO user_tickets VALUES(22,40,227,227,'Эту заявку нужно снять','2026-11-22T17:50:53.731051+00:00',1,'2026-11-22T17:53:34.628188+00:00','');
INSERT INTO user_tickets VALUES(23,40,227,227,'Эту заявку перевести в suspended','2026-11-22T17:51:37.140197+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(24,40,226,226,'Заявка с комментарием','2026-11-23T10:46:29.894605+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(25,40,226,227,'Заявка с комментарием','2026-11-23T11:44:03.560514+00:00',1,NULL,'');
INSERT INTO user_tickets VALUES(26,40,226,226,'string','2026-11-24T12:15:13.453035+00:00',0,NULL,'');
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
    urgency_level TEXT NOT NULL DEFAULT 'normal',
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
INSERT INTO tickets VALUES(6,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-10-01T14:18:02.727712+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,'2026-10-01T14:21:52.567390+00:00',2);
INSERT INTO tickets VALUES(7,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:15.345594+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,NULL,3);
INSERT INTO tickets VALUES(8,36,NULL,NULL,NULL,3,'string',NULL,'2026-10-01T14:42:35.006642+00:00',0,'2026-10-01T13:30:07.599000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(9,32,199,199,1,2,'Не печатает принтер',NULL,'2026-10-01T15:52:19.558984+00:00',1,NULL,'normal',0,'2026-10-01T16:40:17.085905+00:00',10);
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
INSERT INTO tickets VALUES(31,36,NULL,NULL,NULL,NULL,'string',NULL,'2026-10-20T20:06:13.712384+00:00',0,'2026-10-20T19:42:39.647000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(32,32,NULL,NULL,NULL,NULL,'string',NULL,'2026-11-17T20:40:19.499616+00:00',0,'2026-11-17T20:09:11.001000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(33,32,NULL,NULL,NULL,NULL,'string',NULL,'2026-11-17T20:41:47.573934+00:00',0,'2026-11-17T20:09:11.001000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(34,32,NULL,NULL,NULL,NULL,'string',NULL,'2026-11-17T20:45:30.755102+00:00',0,'2026-11-17T20:09:11.001000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(35,32,NULL,NULL,NULL,NULL,'string',NULL,'2026-11-17T20:52:51.958323+00:00',0,'2026-11-17T20:09:11.001000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(40,32,218,200,18,2,'string',NULL,'2026-11-18T15:15:53.040361+00:00',0,NULL,'normal',181,NULL,9);
INSERT INTO tickets VALUES(41,40,NULL,NULL,NULL,2,'Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач','Описание заявки','2026-11-21T08:13:03.516555+00:00',0,'2026-11-22T08:13:03.516555+00:00','normal',0,'2026-11-21T11:08:19.755078+00:00',20);
INSERT INTO tickets VALUES(42,40,NULL,NULL,NULL,2,'Заявка которую надо будет снять',NULL,'2026-11-22T10:57:21.313425+00:00',0,'2026-11-22T10:56:19.404000+00:00','normal',0,'2026-11-22T11:02:21.531313+00:00',4);
INSERT INTO tickets VALUES(43,40,NULL,NULL,NULL,2,'Заявка созданная инженером',NULL,'2026-11-22T11:24:51.293828+00:00',0,'2026-11-22T10:56:19.404000+00:00','normal',0,'2026-11-22T11:36:24.640813+00:00',4);
INSERT INTO tickets VALUES(44,40,NULL,NULL,NULL,2,'Заявка созданная менеджером',NULL,'2026-11-22T12:00:26.135715+00:00',0,'2026-11-22T10:56:19.404000+00:00','normal',0,'2026-11-22T12:06:10.358214+00:00',6);
INSERT INTO tickets VALUES(45,40,NULL,NULL,NULL,2,'Заявка для горячей линии',NULL,'2026-11-22T12:08:30.666317+00:00',1,'2026-11-22T10:56:19.404000+00:00','normal',0,'2026-11-22T12:13:59.148023+00:00',3);
INSERT INTO tickets VALUES(46,40,NULL,NULL,NULL,5,'Заявка созданная обычным пользователем','Я не знаю, позвонили, я внес','2026-11-22T12:17:00.532461+00:00',1,'2026-11-22T10:56:19.404000+00:00','normal',0,'2026-11-22T12:42:24.977757+00:00',10);
INSERT INTO tickets VALUES(47,40,226,226,19,2,'Нам позвонил пользователь клиента',NULL,'2026-11-22T12:46:09.704317+00:00',1,'2026-11-22T12:44:11.813000+00:00','normal',0,'2026-11-22T17:47:10.081904+00:00',5);
INSERT INTO tickets VALUES(48,40,226,226,20,NULL,'Пользователь клиента делает заявку',NULL,'2026-11-22T17:06:02.665451+00:00',0,NULL,'normal',0,'2026-11-22T17:37:33.927763+00:00',1);
INSERT INTO tickets VALUES(49,40,226,226,21,2,'Пользователь клиента делает заявку еще раз',NULL,'2026-11-22T17:09:18.211010+00:00',1,NULL,'normal',0,'2026-11-22T17:26:22.203609+00:00',7);
INSERT INTO tickets VALUES(50,40,227,227,22,NULL,'Эту заявку нужно снять',NULL,'2026-11-22T17:50:53.731378+00:00',0,NULL,'normal',0,'2026-11-22T17:53:34.628046+00:00',1);
INSERT INTO tickets VALUES(51,40,227,227,23,NULL,'Эту заявку перевести в suspended',NULL,'2026-11-22T17:51:37.140585+00:00',0,NULL,'normal',0,'2026-11-22T17:55:37.414460+00:00',1);
INSERT INTO tickets VALUES(52,41,NULL,NULL,NULL,NULL,'Заявка от нового клиента',NULL,'2026-11-23T10:05:36.633246+00:00',0,'2026-11-23T10:05:18.872000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(53,40,226,226,24,NULL,'Заявка с комментарием',NULL,'2026-11-23T10:46:29.894998+00:00',0,'2026-11-23T10:40:22.499000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(54,40,226,227,25,NULL,'Заявка с комментарием',NULL,'2026-11-23T11:44:03.560853+00:00',0,'2026-11-23T10:40:22.499000+00:00','normal',0,NULL,0);
INSERT INTO tickets VALUES(55,40,226,226,26,NULL,'string',NULL,'2026-11-24T12:15:13.453971+00:00',0,NULL,'normal',0,NULL,0);
INSERT INTO tickets VALUES(56,32,NULL,NULL,NULL,2,'Заявка для горячей линии',NULL,'2026-11-27T14:45:39.862918+00:00',1,NULL,'normal',223,NULL,2);
INSERT INTO tickets VALUES(57,32,NULL,218,NULL,2,'Просто заявка',NULL,'2026-11-27T14:45:50.182337+00:00',0,NULL,'normal',223,NULL,4);
INSERT INTO tickets VALUES(58,32,NULL,200,NULL,2,'Заявка от инженера',NULL,'2026-11-27T15:06:59.135476+00:00',0,NULL,'normal',0,NULL,1);
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
INSERT INTO ticket_status_records VALUES(43,9,181,'accepted','2026-10-01T16:25:40.893642+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(44,3,181,'assigned','2026-10-01T16:27:13.462054+00:00',122,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(46,9,181,'assigned','2026-10-01T16:39:41.948909+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(47,9,181,'at_work','2026-10-01T16:40:10.030911+00:00',NULL,NULL,NULL,1,'erfref',0);
INSERT INTO ticket_status_records VALUES(48,9,181,'ready_for_review','2026-10-01T16:40:17.085589+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(49,9,181,'executed','2026-10-01T16:40:17.085905+00:00',NULL,NULL,NULL,NULL,'',0);
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
INSERT INTO ticket_status_records VALUES(105,18,181,'suspended','2026-10-05T14:34:39.016636+00:00',NULL,NULL,NULL,NULL,'',0);
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
INSERT INTO ticket_status_records VALUES(122,20,181,'ready_for_review','2026-10-05T14:49:33.790681+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(123,20,181,'executed','2026-10-05T14:49:33.790774+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(124,21,181,'created','2026-10-05T14:49:55.053814+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(125,21,181,'accepted','2026-10-05T14:49:55.053913+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(126,21,181,'assigned','2026-10-05T14:49:58.342010+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(127,21,181,'at_work','2026-10-05T14:50:00.555768+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(128,21,181,'ready_for_review','2026-10-05T14:57:21.394379+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(129,21,181,'executed','2026-10-05T14:57:21.394454+00:00',NULL,NULL,NULL,NULL,'',0);
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
INSERT INTO ticket_status_records VALUES(166,28,181,'created','2026-10-06T11:36:54.745452+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(167,28,181,'accepted','2026-10-06T11:36:54.745821+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(168,13,181,'suspended','2026-10-06T11:51:21.020475+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(169,28,181,'suspended','2026-10-06T11:51:21.020660+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(171,29,181,'created','2026-10-06T11:53:16.687858+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(172,29,181,'accepted','2026-10-06T11:53:16.688504+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(173,29,181,'suspended','2026-10-06T11:53:37.685194+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(174,30,181,'created','2026-10-09T09:01:12.976374+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(175,30,181,'accepted','2026-10-09T09:01:12.976689+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(182,31,181,'created','2026-10-20T20:06:13.712384+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(183,31,181,'accepted','2026-10-20T20:06:13.712473+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(184,32,181,'created','2026-11-17T20:40:19.499616+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(185,32,181,'accepted','2026-11-17T20:40:21.912684+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(186,33,181,'created','2026-11-17T20:41:47.573934+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(187,33,181,'accepted','2026-11-17T20:41:49.959406+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(188,34,181,'created','2026-11-17T20:45:30.755102+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(189,34,181,'accepted','2026-11-17T20:45:34.173251+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(190,35,181,'created','2026-11-17T20:52:51.958323+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(191,35,181,'accepted','2026-11-17T20:52:53.372337+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(200,40,181,'created_from_request_user','2026-11-18T15:15:53.040361+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(201,40,181,'accepted','2026-11-18T15:15:53.040899+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(202,40,181,'deferred','2026-11-18T15:33:28.639458+00:00',NULL,NULL,NULL,NULL,'edqedrwefwf',0);
INSERT INTO ticket_status_records VALUES(203,40,181,'assigned','2026-11-18T15:34:20.763144+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(204,40,181,'at_work','2026-11-18T15:35:04.117963+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(205,40,181,'ready_for_review','2026-11-18T15:35:35.061026+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(206,40,181,'assigned','2026-11-18T15:36:35.215169+00:00',181,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(207,41,222,'created','2026-11-21T08:13:03.516555+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(208,41,222,'accepted','2026-11-21T08:13:03.516772+00:00',NULL,NULL,NULL,NULL,'Комментарий',0);
INSERT INTO ticket_status_records VALUES(209,41,224,'assigned','2026-11-21T09:46:54.896572+00:00',221,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(210,41,221,'at_work','2026-11-21T09:49:19.630391+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(211,41,221,'ready_for_review','2026-11-21T09:50:20.684026+00:00',NULL,NULL,NULL,NULL,'Не успел доделать',0);
INSERT INTO ticket_status_records VALUES(212,41,224,'assigned','2026-11-21T09:53:53.365609+00:00',221,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(213,41,224,'accepted','2026-11-21T09:58:19.082913+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(214,41,224,'assigned','2026-11-21T10:00:32.689797+00:00',221,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(215,41,221,'at_work','2026-11-21T10:01:30.688610+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(216,41,221,'ready_for_review','2026-11-21T10:01:38.530648+00:00',NULL,NULL,NULL,NULL,'Не успел доделать',0);
INSERT INTO ticket_status_records VALUES(217,41,224,'assigned','2026-11-21T10:05:08.986762+00:00',221,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(218,41,224,'assigned','2026-11-21T10:06:32.641874+00:00',221,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(219,41,221,'at_work','2026-11-21T10:08:13.764857+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(220,41,221,'ready_for_review','2026-11-21T10:08:19.221327+00:00',NULL,NULL,NULL,NULL,'Не успел доделать',0);
INSERT INTO ticket_status_records VALUES(221,41,224,'accepted','2026-11-21T10:35:23.713850+00:00',NULL,NULL,NULL,NULL,'не хватило времени',0);
INSERT INTO ticket_status_records VALUES(222,41,224,'assigned','2026-11-21T10:37:09.410523+00:00',223,NULL,NULL,NULL,'теперь попробуем инженера с ролью удаленщика',0);
INSERT INTO ticket_status_records VALUES(223,41,223,'at_work','2026-11-21T11:02:12.532173+00:00',NULL,'2026-11-21T09:50:27.175000+00:00','2026-11-21T09:58:27.175000+00:00',0,'',0);
INSERT INTO ticket_status_records VALUES(224,41,223,'ready_for_review','2026-11-21T11:02:12.532173+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(225,41,224,'assigned','2026-11-21T11:03:50.586964+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(226,41,223,'at_work','2026-11-21T11:06:15.687489+00:00',NULL,NULL,NULL,0,'',100);
INSERT INTO ticket_status_records VALUES(227,41,223,'ready_for_review','2026-11-21T11:06:15.687489+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(228,41,222,'executed','2026-11-21T11:08:19.755078+00:00',NULL,NULL,NULL,NULL,'Сделали заявку',0);
INSERT INTO ticket_status_records VALUES(229,42,224,'created','2026-11-22T10:57:21.313425+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(230,42,224,'accepted','2026-11-22T10:57:26.721422+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(231,42,224,'assigned','2026-11-22T10:59:58.878514+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(232,42,224,'deferred','2026-11-22T11:00:43.031517+00:00',NULL,NULL,NULL,NULL,'Пока отложим',0);
INSERT INTO ticket_status_records VALUES(233,42,224,'assigned','2026-11-22T11:00:53.611424+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(234,42,224,'cancelled','2026-11-22T11:02:21.531313+00:00',NULL,NULL,NULL,NULL,'Заявку снимаем',0);
INSERT INTO ticket_status_records VALUES(235,43,221,'created','2026-11-22T11:24:51.293828+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(236,43,224,'accepted','2026-11-22T11:30:53.367165+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(237,43,224,'assigned','2026-11-22T11:31:20.671847+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(238,43,221,'at_work','2026-11-22T11:33:02.891017+00:00',NULL,NULL,NULL,1,'',3500);
INSERT INTO ticket_status_records VALUES(239,43,221,'ready_for_review','2026-11-22T11:33:02.891017+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(240,43,224,'executed','2026-11-22T11:36:24.640813+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(241,44,224,'created','2026-11-22T12:00:26.135715+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(242,44,224,'accepted','2026-11-22T12:00:29.019513+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(243,44,224,'assigned','2026-11-22T12:02:40.155294+00:00',222,NULL,NULL,NULL,'Будет выполнять опытный инженер',0);
INSERT INTO ticket_status_records VALUES(244,44,222,'at_work','2026-11-22T12:03:33.191280+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(245,44,222,'paused','2026-11-22T12:04:07.042305+00:00',NULL,NULL,NULL,NULL,'на паузу',0);
INSERT INTO ticket_status_records VALUES(246,44,222,'at_work','2026-11-22T12:04:46.814998+00:00',NULL,NULL,NULL,0,'Возвращаем в работу',0);
INSERT INTO ticket_status_records VALUES(247,44,222,'ready_for_review','2026-11-22T12:05:00.121206+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(248,44,222,'executed','2026-11-22T12:06:10.358214+00:00',NULL,NULL,NULL,NULL,'Сам подтвердил свою работу',0);
INSERT INTO ticket_status_records VALUES(249,45,224,'created','2026-11-22T12:08:30.666317+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(250,45,224,'accepted','2026-11-22T12:08:34.795039+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(251,45,223,'assigned','2026-11-22T12:10:35.151404+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(252,45,223,'at_work','2026-11-22T12:10:35.151404+00:00',NULL,NULL,NULL,1,'',0);
INSERT INTO ticket_status_records VALUES(253,45,223,'ready_for_review','2026-11-22T12:12:27.265240+00:00',NULL,NULL,NULL,NULL,'Завершаем заявку на горячей линии',0);
INSERT INTO ticket_status_records VALUES(254,45,224,'executed','2026-11-22T12:13:59.148023+00:00',NULL,NULL,NULL,NULL,'Подтверждение заявки на горячей линнии',0);
INSERT INTO ticket_status_records VALUES(255,46,220,'created','2026-11-22T12:17:00.532461+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(256,46,224,'accepted','2026-11-22T12:18:08.811201+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(257,46,224,'assigned','2026-11-22T12:31:16.825126+00:00',222,NULL,NULL,NULL,'Будет выполнять опытный инженер',0);
INSERT INTO ticket_status_records VALUES(258,46,222,'at_work','2026-11-22T12:36:52.227833+00:00',NULL,'2026-11-22T11:36:32.780000+00:00','2026-11-22T12:36:32.780000+00:00',0,'',0);
INSERT INTO ticket_status_records VALUES(259,46,222,'ready_for_review','2026-11-22T12:36:52.227833+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(260,46,224,'accepted','2026-11-22T12:39:14.077503+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(261,46,224,'assigned','2026-11-22T12:40:02.520113+00:00',228,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(262,46,228,'at_work','2026-11-22T12:41:17.367461+00:00',NULL,NULL,NULL,0,'',0);
INSERT INTO ticket_status_records VALUES(263,46,228,'ready_for_review','2026-11-22T12:41:29.220774+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(264,46,224,'executed','2026-11-22T12:42:24.977757+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(265,47,222,'created_from_request_user','2026-11-22T12:46:09.704317+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(266,47,222,'accepted','2026-11-22T12:46:14.070085+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(271,48,NULL,'created_from_ticket_user','2026-11-22T17:06:02.665451+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(272,49,NULL,'created_from_ticket_user','2026-11-22T17:09:18.211010+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(273,49,224,'accepted','2026-11-22T17:14:58.826220+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(274,49,224,'assigned','2026-11-22T17:17:21.572011+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(275,49,223,'at_work','2026-11-22T17:20:15.126673+00:00',NULL,NULL,NULL,1,'',0);
INSERT INTO ticket_status_records VALUES(276,49,223,'ready_for_review','2026-11-22T17:21:40.275342+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(277,49,NULL,'confirmed_by_user','2026-11-22T17:26:22.203609+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(278,48,NULL,'cancelled_by_user','2026-11-22T17:37:33.927763+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(279,47,223,'assigned','2026-11-22T17:45:49.184380+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(280,47,223,'at_work','2026-11-22T17:45:49.184380+00:00',NULL,NULL,NULL,1,'',0);
INSERT INTO ticket_status_records VALUES(281,47,223,'ready_for_review','2026-11-22T17:45:59.932344+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(282,47,224,'executed','2026-11-22T17:47:10.081904+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(283,50,NULL,'created_from_ticket_user','2026-11-22T17:50:53.731378+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(284,51,NULL,'created_from_ticket_user','2026-11-22T17:51:37.140585+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(285,50,224,'rejected','2026-11-22T17:53:34.628046+00:00',NULL,NULL,NULL,NULL,'Отказали',0);
INSERT INTO ticket_status_records VALUES(286,51,224,'suspended','2026-11-22T17:55:37.414460+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(287,52,224,'created','2026-11-23T10:05:36.633246+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(288,52,224,'accepted','2026-11-23T10:05:36.634713+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(289,53,224,'created_from_request_user','2026-11-23T10:46:29.894998+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(290,53,224,'accepted','2026-11-23T10:46:29.895335+00:00',NULL,NULL,NULL,NULL,'Комментарий',0);
INSERT INTO ticket_status_records VALUES(291,54,224,'created_from_request_user','2026-11-23T11:44:03.560853+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(292,54,224,'accepted','2026-11-23T11:44:03.561148+00:00',NULL,NULL,NULL,NULL,'Комментарий',0);
INSERT INTO ticket_status_records VALUES(293,55,NULL,'created_from_ticket_user','2026-11-24T12:15:13.453971+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(294,56,224,'created','2026-11-27T14:45:39.862918+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(295,56,224,'accepted','2026-11-27T14:45:39.863127+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(296,57,224,'created','2026-11-27T14:45:50.182337+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(297,57,224,'accepted','2026-11-27T14:45:50.182550+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(298,57,181,'assigned','2026-11-27T15:00:48.633675+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(299,56,223,'assigned','2026-11-27T15:04:20.546928+00:00',223,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(300,56,223,'at_work','2026-11-27T15:04:20.546928+00:00',NULL,NULL,NULL,1,'',0);
INSERT INTO ticket_status_records VALUES(301,56,223,'ready_for_review','2026-11-27T15:04:32.648790+00:00',NULL,NULL,NULL,NULL,'',0);
INSERT INTO ticket_status_records VALUES(302,58,223,'created','2026-11-27T15:06:59.135476+00:00',NULL,NULL,NULL,NULL,'',0);
CREATE TABLE auth_refresh_sessions (
    token_hash TEXT NOT NULL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('admin', 'user')),
    username TEXT NOT NULL,
    created_at DOUBLE PRECISION NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    scope TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);
INSERT INTO auth_refresh_sessions VALUES('459072c561f66fb26def04009d0e2e3afddf5310461417892f8f0fa2524cedf4',606,224,'admin','manager',1795790593.971915,1796395393.971915,'[]');
INSERT INTO auth_refresh_sessions VALUES('1c86ad0b789eeb079b4e6c2960e02c2c4448a3370c4f90e7ecb61cb26677b7cf',606,224,'admin','manager',1795790679.62087798,1796395479.62087798,'[]');
INSERT INTO auth_refresh_sessions VALUES('289f3193f86851d79e7f8eab0155f90e8201812560f1927750bd3b3082e0ac9f',525,181,'admin','tega',1795792057.2876091,1796396857.2876091,'[]');
INSERT INTO auth_refresh_sessions VALUES('a26117b0a4c0e45518b6660c15b77b89fc1277d01c0f8a75a1c9a3c873a52b63',604,223,'admin','remote_engineer',1795792158.53990101,1796396958.53990101,'[]');
INSERT INTO auth_refresh_sessions VALUES('9ae14b11dc6f47e5ecb8b6e628ade935f8f89aab959e919bd125e8aa97f919f1',604,223,'admin','remote_engineer',1795792261.16097593,1796397061.16097593,'[]');
INSERT INTO auth_refresh_sessions VALUES('d9cd4e820b02b27be2c147b5788a233c3e7209331fd4c4b75cf72ec8fc738e3b',604,223,'admin','remote_engineer',1795792661.7411611,1796397461.7411611,'[]');
INSERT INTO auth_refresh_sessions VALUES('415a7985814f2b4f1a72a7361ceeeb2c76390bd5a42bcedcad57eb9b57802929',604,223,'admin','remote_engineer',1795792914.92608809,1796397714.92608809,'[]');
INSERT INTO auth_refresh_sessions VALUES('5feb93031b769333cc8db2029c528875ad7468482c561624ffbc04df020e0fa0',604,223,'admin','remote_engineer',1795793163.91259002,1796397963.91259002,'[]');
CREATE TABLE creation_results (
    employee_id INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    status_code INTEGER,
    body TEXT,
    expires_at DOUBLE PRECISION,
    PRIMARY KEY (employee_id, idempotency_key),
    CHECK ((status_code IS NULL AND body IS NULL AND expires_at IS NULL)
        OR (status_code IS NOT NULL AND status_code BETWEEN 200 AND 299 AND body IS NOT NULL))
);
INSERT INTO creation_results VALUES(224,'d2072fc50c4e6b5bd4eeb3687725196a','aa905a3441983df5c12cc8b988509a2cd04b179ad9535ba1b000ec233c7e33d3',201,'{"ticket_id":56,"client_id":32,"user_id":0,"contact_user_id":0,"user_ticket_id":0,"department_id":2,"text_of_ticket":"Заявка для горячей линии","description":"","date_created":"2026-11-27T14:45:39.862918Z","date_finished":null,"planned_at":null,"remote_work_recommended":true,"urgency":"normal","current_executor_id":0,"last_executor_id":0,"is_closed":false,"time_spent":0,"statuses":[{"id":294,"status":"created","actor_id":224,"executor_id":0,"date_created":"2026-11-27T14:45:39.862918Z","actual_started_at":null,"actual_finished_at":null,"duration":"PT0S","work_is_remote":null,"comment":""},{"id":295,"status":"accepted","actor_id":224,"executor_id":0,"date_created":"2026-11-27T14:45:39.863127Z","actual_started_at":null,"actual_finished_at":null,"duration":"PT0S","work_is_remote":null,"comment":""}],"comments":[]}',1795877139.87646198);
INSERT INTO creation_results VALUES(224,'2199b40557108a37199342f34a01f28e','5594219a376bd2fe221a85d4fda7606552628422f3ee455146cf82a5c37b1c12',201,'{"ticket_id":57,"client_id":32,"user_id":0,"contact_user_id":0,"user_ticket_id":0,"department_id":0,"text_of_ticket":"Просто заявка","description":"","date_created":"2026-11-27T14:45:50.182337Z","date_finished":null,"planned_at":null,"remote_work_recommended":false,"urgency":"normal","current_executor_id":0,"last_executor_id":0,"is_closed":false,"time_spent":0,"statuses":[{"id":296,"status":"created","actor_id":224,"executor_id":0,"date_created":"2026-11-27T14:45:50.182337Z","actual_started_at":null,"actual_finished_at":null,"duration":"PT0S","work_is_remote":null,"comment":""},{"id":297,"status":"accepted","actor_id":224,"executor_id":0,"date_created":"2026-11-27T14:45:50.182550Z","actual_started_at":null,"actual_finished_at":null,"duration":"PT0S","work_is_remote":null,"comment":""}],"comments":[]}',1795877150.19042301);
INSERT INTO creation_results VALUES(223,'82c6c5e5a2f7c5bf8dcbb9a3a431f81e','8ed812848e6dc45868f2b4923c7620d9891bf8c678f47f0918ecd0fb171305be',201,'{"ticket_id":58,"client_id":32,"user_id":0,"contact_user_id":0,"user_ticket_id":0,"department_id":2,"text_of_ticket":"Заявка от инженера","description":"","date_created":"2026-11-27T15:06:59.135476Z","date_finished":null,"planned_at":null,"remote_work_recommended":false,"urgency":"normal","current_executor_id":0,"last_executor_id":0,"is_closed":false,"time_spent":0,"statuses":[{"id":302,"status":"created","actor_id":223,"executor_id":0,"date_created":"2026-11-27T15:06:59.135476Z","actual_started_at":null,"actual_finished_at":null,"duration":"PT0S","work_is_remote":null,"comment":""}],"comments":[]}',1795878419.14786505);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('accounts',626);
INSERT INTO sqlite_sequence VALUES('clients',41);
INSERT INTO sqlite_sequence VALUES('departments',9);
INSERT INTO sqlite_sequence VALUES('employees',230);
INSERT INTO sqlite_sequence VALUES('roles',88);
INSERT INTO sqlite_sequence VALUES('ticket_comments',17);
INSERT INTO sqlite_sequence VALUES('ticket_status_records',302);
INSERT INTO sqlite_sequence VALUES('tickets',58);
INSERT INTO sqlite_sequence VALUES('user_tickets',26);
INSERT INTO sqlite_sequence VALUES('user_tickets_comment',6);
INSERT INTO sqlite_sequence VALUES('user_tickets_status_record',113);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
CREATE UNIQUE INDEX idx_departments_name
ON departments(name);
CREATE INDEX idx_ticket_comments_ticket_id
ON ticket_comments(ticket_id, ticket_comment_id);
CREATE INDEX idx_ticket_comments_employee_id
ON ticket_comments(employee_id);
CREATE INDEX idx_auth_refresh_sessions_subject
    ON auth_refresh_sessions(subject_type, subject_id);
CREATE INDEX idx_auth_refresh_sessions_account
    ON auth_refresh_sessions(account_id);
CREATE INDEX idx_auth_refresh_sessions_expiry
    ON auth_refresh_sessions(expires_at);
CREATE INDEX idx_creation_results_expiry ON creation_results(expires_at);
COMMIT;

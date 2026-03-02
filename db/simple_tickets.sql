PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE employees (
	employee_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	first_name TEXT,
	last_name TEXT,
	email TEXT,
	phone TEXT,
	date_created TEXT,
	address TEXT,
	enabled INTEGER DEFAULT (1),
	is_deleted INTEGER DEFAULT (0),
	version INTEGER
, is_admin INTEGER);
INSERT INTO employees VALUES(2,'1','2','3',NULL,NULL,NULL,1,0,NULL,1);
INSERT INTO employees VALUES(4,'first','last_name','email@email.email','phone','2026-02-19T16:08:55.028177',NULL,1,0,0,1);
INSERT INTO employees VALUES(5,'first','last_name','email@email.email','phone','2026-02-19T16:11:03.355452',NULL,0,0,1,1);
INSERT INTO employees VALUES(6,'first','last_name','email@email.email','phone','2026-02-19T16:11:19.293495',NULL,0,0,1,1);
INSERT INTO employees VALUES(7,'first','last_name','email@email.email','phone','2026-02-19T16:11:46.396481',NULL,0,0,1,1);
INSERT INTO employees VALUES(8,'first','last_name','email@email.email','phone','2026-02-19T16:11:51.815801',NULL,0,0,1,1);
INSERT INTO employees VALUES(9,'first','last_name','email@email.email','phone','2026-02-19T16:11:57.300443',NULL,0,0,1,1);
INSERT INTO employees VALUES(10,'first','last_name','email@email.email','phone','2026-02-19T16:27:07.512491',NULL,0,0,1,1);
INSERT INTO employees VALUES(11,'first','last_name','email@email.email','phone','2026-02-19T16:27:16.037230',NULL,0,0,1,1);
INSERT INTO employees VALUES(12,'first','last_name','email@email.email','phone','2026-02-19T16:28:20.305448',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(13,'first','last_name','email@email.email','phone','2026-02-19T16:28:26.433405',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(14,'first','last_name','email@email.email','phone','2026-02-19T16:32:28.825437',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(15,'first','last_name','email@email.email','phone','2026-02-19T16:32:29.273525',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(16,'first','last_name','email@email.email','phone','2026-02-19T16:32:29.865000',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(17,'first','last_name','email@email.email','phone','2026-02-19T16:44:55.889807',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(18,'first','last_name','email@email.email','phone','2026-02-19T16:45:17.987471',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(19,'first','last_name','email@email.email','phone','2026-02-19T18:29:57.688467',NULL,0,0,1,NULL);
INSERT INTO employees VALUES(20,'None','None','None','None','2026-02-19T18:35:53.721741',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(21,'None','None','None','None','2026-02-19T18:36:05.551171',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(22,'None','None','None','None','2026-02-19T18:37:26.651150',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(23,'None','None','None','None','2026-02-19T18:38:26.877877',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(24,'None','None','None','None','2026-02-19T18:39:04.032588',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(25,'first_name','last_name','None','None','2026-02-19T18:41:20.376339',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(26,'first_name','last_name','','','2026-02-19T18:42:40.513683',NULL,1,0,0,NULL);
INSERT INTO employees VALUES(27,'first_name','last_name','','','2026-02-19T18:43:33.309114',NULL,1,0,0,1);
INSERT INTO employees VALUES(28,'first_name','last_name','','','2026-02-19T18:43:52.597229',NULL,1,0,0,1);
INSERT INTO employees VALUES(29,'first_name','last_name','','','2026-02-19T18:51:28.687242',NULL,1,0,0,1);
INSERT INTO employees VALUES(30,'first_name','last_name','','','2026-02-19T18:56:17.211404',NULL,1,0,0,1);
INSERT INTO employees VALUES(31,'first_name','last_name','','','2026-02-21T13:23:26.534094',NULL,1,0,0,1);
INSERT INTO employees VALUES(32,'first_name','last_name','','','2026-02-21T14:29:15.380839',NULL,1,0,0,1);
INSERT INTO employees VALUES(33,'first_name','last_name','','','2026-02-21T14:29:15.381928',NULL,1,0,0,1);
INSERT INTO employees VALUES(34,'first_name','last_name','','','2026-02-21T14:38:16.302733',NULL,1,0,0,1);
INSERT INTO employees VALUES(35,'first_name','last_name','','','2026-02-21T14:38:16.303235',NULL,1,0,0,1);
INSERT INTO employees VALUES(36,'first_name','last_name','','','2026-02-21T14:45:34.924896',NULL,1,0,1,1);
INSERT INTO employees VALUES(37,'first_name','last_name','','','2026-02-21T14:45:34.926165',NULL,1,0,1,1);
INSERT INTO employees VALUES(38,'first_name','last_name','','','2026-02-21T14:46:26.379592',NULL,1,0,1,1);
INSERT INTO employees VALUES(39,'first_name','last_name','','','2026-02-21T14:46:26.380454',NULL,1,0,1,1);
INSERT INTO employees VALUES(40,'first_name','last_name','','','2026-02-21T14:48:35.415689',NULL,1,0,0,1);
INSERT INTO employees VALUES(41,'first_name','last_name','','','2026-02-21T14:48:35.416313',NULL,1,0,0,1);
INSERT INTO employees VALUES(42,'first_name11111','last_name','','','2026-02-21T15:19:11.867659',NULL,1,0,1,1);
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1)
, version INTEGER);
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	enabled INTEGER DEFAULT (1),
	login TEXT,
	password TEXT,
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO accounts VALUES(1,NULL,1,'login','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-19T18:51:28');
INSERT INTO accounts VALUES(2,30,1,'login1','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-19T18:56:17');
INSERT INTO accounts VALUES(3,33,1,'login11771673355.3818662','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-21T14:29:15');
INSERT INTO accounts VALUES(4,35,1,'login11771673896.3032212','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-21T14:38:16');
INSERT INTO accounts VALUES(5,34,1,'login21771673896.3038576','76c7e935b12e2ffd303018fb23b1919ab65b31e4003078bfbd8fec04c8768e76','2026-02-21T14:38:16');
INSERT INTO accounts VALUES(6,37,1,'login11771674334.926153','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-21T14:45:34');
INSERT INTO accounts VALUES(7,39,1,'login11771674386.3804402','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-21T14:46:26');
INSERT INTO accounts VALUES(8,41,1,'login11771674515.4162424','6e866f893e64abaacda283976d6b3fd7ac2fcc708e42687193d3dbbe1249544b','2026-02-21T14:48:35');
CREATE TABLE admins (
	admin_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	job_title TEXT,
	CONSTRAINT employee_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
	
);
INSERT INTO admins VALUES(2,4,'');
INSERT INTO admins VALUES(3,5,'');
INSERT INTO admins VALUES(4,6,'');
INSERT INTO admins VALUES(5,7,'');
INSERT INTO admins VALUES(6,8,'');
INSERT INTO admins VALUES(7,9,'');
INSERT INTO admins VALUES(8,10,'');
INSERT INTO admins VALUES(9,11,'');
INSERT INTO admins VALUES(10,12,'');
INSERT INTO admins VALUES(11,13,'');
INSERT INTO admins VALUES(12,14,'');
INSERT INTO admins VALUES(13,15,'');
INSERT INTO admins VALUES(14,16,'');
INSERT INTO admins VALUES(15,17,'');
INSERT INTO admins VALUES(16,18,'');
INSERT INTO admins VALUES(17,19,'');
INSERT INTO admins VALUES(18,20,'');
INSERT INTO admins VALUES(19,21,'');
INSERT INTO admins VALUES(20,22,'');
INSERT INTO admins VALUES(21,23,'');
INSERT INTO admins VALUES(22,24,'');
INSERT INTO admins VALUES(23,25,'');
INSERT INTO admins VALUES(24,26,'');
INSERT INTO admins VALUES(25,27,'');
INSERT INTO admins VALUES(26,28,'');
INSERT INTO admins VALUES(27,29,'');
INSERT INTO admins VALUES(28,30,'');
INSERT INTO admins VALUES(29,31,'');
INSERT INTO admins VALUES(30,32,'');
INSERT INTO admins VALUES(31,33,'');
INSERT INTO admins VALUES(32,34,'');
INSERT INTO admins VALUES(33,35,'');
INSERT INTO admins VALUES(34,36,'');
INSERT INTO admins VALUES(35,37,'');
INSERT INTO admins VALUES(36,38,'');
INSERT INTO admins VALUES(37,39,'');
INSERT INTO admins VALUES(38,40,'');
INSERT INTO admins VALUES(39,41,'');
INSERT INTO admins VALUES(40,42,NULL);
CREATE TABLE admins_roles (
	admin_role INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	role_id INTEGER,
	CONSTRAINT admins_roles_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict,
	CONSTRAINT admins_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id) on DELETE restrict
);
CREATE TABLE clients (
	client_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	address TEXT,
	email TEXT,
	phone TEXT,
	admin_id INTEGER,
	date_created INTEGER,
	enabled INTEGER, version INTEGER,
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict
);
CREATE TABLE tickets (
	ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER,
	admin_id INTEGER,
	user_id INTEGER,
	user_ticket_contact_user_id INTEGER DEFAULT(0),
	user_ticket_id INTEGER,
	description TEXT,
	text_of_ticket TEXT,
	date_created TEXT,
	is_remote INTEGER DEFAULT (0),
	is_finished INTEGER DEFAULT (0),
	date_finished INTEGER,
	vesrion INTEGER,
	urgency_level INTEGER,
	CONSTRAINT tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict,
	CONSTRAINT tickets_user_user_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES users(user_id) on delete restrict
);
CREATE TABLE IF NOT EXISTS "tickets_comment" (
	comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	comment TEXT,
	ticket_id INTEGER,
	admin_id INTEGER,
	date_created TEXT,
	CONSTRAINT comment_tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict
);
CREATE TABLE IF NOT EXISTS "tickets_executor_assigments" (
	executor_assigment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	date_assigment TEXT,
	ticket_id INTEGER,
	CONSTRAINT executor_assigments_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete RESTRICT,
	CONSTRAINT executor_assigments_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on DELETE restrict
);
CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict
);
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER,
	user_id INTEGER,
	user_ticket_contact_user_id INTEGER DEFAULT(0),
	description TEXT,
	date_created TEXT,
	version INTEGER,
	date_finished TEXT,
	is_closed INTEGER,
	promoted_ticket_id INTEGER,
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_tickets_FK FOREIGN KEY (promoted_ticket_id) REFERENCES tickets(ticket_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES users(user_id) on delete restrict

);
CREATE TABLE IF NOT EXISTS "user_tickets_comment" (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	comment TEXT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
CREATE TABLE users (
	user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	client_id INTEGER,
	CONSTRAINT users_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT users_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on DELETE restrict
);
CREATE TABLE users_roles (
	user_role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	role_id INTEGER,
	user_id INTEGER,
	CONSTRAINT users_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id) on delete restrict,
	CONSTRAINT users_roles_users_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict
);
CREATE TABLE IF NOT EXISTS "uset_tickets_executor_assigments" (
	user_executor_assigment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	date_assigment TEXT,
	user_ticket_id INTEGER,
	CONSTRAINT executor_assigments_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict,
	CONSTRAINT executor_assigments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',42);
INSERT INTO sqlite_sequence VALUES('admins',40);
INSERT INTO sqlite_sequence VALUES('accounts',8);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
COMMIT;

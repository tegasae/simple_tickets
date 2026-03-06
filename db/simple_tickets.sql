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
	version INTEGER,
	is_admin INTEGER);
INSERT INTO employees VALUES(1,'John','Smith','john.smith@company.com','','2026-03-05T11:04:11',NULL,0,6,1);
INSERT INTO employees VALUES(2,'John','Smith','john.smith@company.com','','2026-03-05T11:23:24',NULL,0,7,1);
INSERT INTO employees VALUES(3,'John','Smith','john.smith@company.com','','2026-03-05T11:29:03',NULL,0,7,1);
INSERT INTO employees VALUES(4,'John','Smith','john.smith@company.com','','2026-03-05T11:29:33',NULL,0,7,1);
INSERT INTO employees VALUES(5,'John','Smith','john.smith@company.com','','2026-03-05T13:11:58',NULL,0,10,1);
INSERT INTO employees VALUES(6,'John','Smith','john.smith@company.com','','2026-03-05T18:58:24',NULL,0,10,1);
INSERT INTO employees VALUES(7,'John','Smith','john.smith@company.com','','2026-03-05T20:48:36',NULL,0,10,1);
INSERT INTO employees VALUES(8,'John','Smith','','','1772733320',NULL,1,1,0);
INSERT INTO employees VALUES(9,'John','Smith','','','1772733339',NULL,1,1,0);
INSERT INTO employees VALUES(10,'John','Smith','','','1772733448',NULL,1,1,0);
INSERT INTO employees VALUES(11,'John','Smith','','','1772733502',NULL,1,1,0);
INSERT INTO employees VALUES(12,'John','Smith','','','1772733570',NULL,1,1,0);
INSERT INTO employees VALUES(13,'John','Smith','john.smith@company.com','','2026-03-05T21:01:04',NULL,1,6,1);
INSERT INTO employees VALUES(14,'John','Smith','john.smith@company.com','','2026-03-05T21:02:08',NULL,1,6,1);
INSERT INTO employees VALUES(15,'John','Smith','john.smith@company.com','','2026-03-05T21:03:24',NULL,1,6,1);
INSERT INTO employees VALUES(16,'John','Smith','john.smith@company.com','','2026-03-05T21:04:15',NULL,1,6,1);
INSERT INTO employees VALUES(17,'John','Smith','','','2026-03-06T09:47:06',NULL,1,0,1);
INSERT INTO employees VALUES(18,'John','Smith','','','2026-03-06T09:47:56',NULL,1,0,1);
INSERT INTO employees VALUES(19,'John','Smith','','','2026-03-06T09:48:45',NULL,1,0,1);
INSERT INTO employees VALUES(20,'John','Smith','','','2026-03-06T09:49:31',NULL,1,0,1);
INSERT INTO employees VALUES(21,'John','Smith','','','2026-03-06T09:50:40',NULL,1,0,1);
INSERT INTO employees VALUES(22,'John','Smith','','','2026-03-06T09:51:05',NULL,1,0,1);
INSERT INTO employees VALUES(23,'John','Smith','','','2026-03-06T09:52:15',NULL,1,0,1);
INSERT INTO employees VALUES(24,'John','Smith','','','2026-03-06T09:52:40',NULL,1,0,1);
INSERT INTO employees VALUES(25,'John','Smith','','','2026-03-06T09:52:49',NULL,1,0,1);
INSERT INTO employees VALUES(26,'John','Smith','','','2026-03-06T09:53:04',NULL,1,0,1);
INSERT INTO employees VALUES(27,'John','Smith','','','2026-03-06T09:58:42',NULL,1,0,1);
INSERT INTO employees VALUES(28,'John','Smith','','','2026-03-06T10:02:29',NULL,1,0,1);
INSERT INTO employees VALUES(29,'John','Smith','','','2026-03-06T10:03:23',NULL,1,0,1);
INSERT INTO employees VALUES(30,'John','Smith','','','2026-03-06T10:04:33',NULL,1,0,1);
INSERT INTO employees VALUES(31,'John','Smith','','','2026-03-06T10:06:38',NULL,1,0,1);
INSERT INTO employees VALUES(32,'John','Smith','','','2026-03-06T10:07:02',NULL,1,0,1);
INSERT INTO employees VALUES(33,'John','Smith','','','2026-03-06T10:10:07',NULL,1,0,1);
INSERT INTO employees VALUES(34,'John','Smith','','','2026-03-06T10:11:14',NULL,1,0,1);
INSERT INTO employees VALUES(36,'John','Smith','','','2026-03-06T10:16:57',NULL,1,0,1);
INSERT INTO employees VALUES(37,'John','Smith','','','2026-03-06T10:17:23',NULL,1,0,1);
INSERT INTO employees VALUES(38,'John','Smith','','','2026-03-06T10:18:54',NULL,1,0,1);
INSERT INTO employees VALUES(39,'John','Smith','john.smith@company.com','','2026-03-06T10:20:13',NULL,1,1,1);
INSERT INTO employees VALUES(40,'John','Smith','john.smith@company.com','','2026-03-06T10:23:02',NULL,1,2,1);
INSERT INTO employees VALUES(41,'John','Smith','','','2026-03-06T10:24:09',NULL,1,0,1);
INSERT INTO employees VALUES(42,'John','Smith','john.smith@company.com','','2026-03-06T10:24:37',NULL,1,4,1);
INSERT INTO employees VALUES(43,'John','Smith','john.smith@company.com','','2026-03-06T10:25:58',NULL,1,7,1);
INSERT INTO employees VALUES(44,'John','Smith','','','2026-03-06T10:26:36',NULL,1,0,1);
INSERT INTO employees VALUES(45,'John','Smith','john.smith@company.com','','2026-03-06T10:26:47',NULL,1,8,1);
INSERT INTO employees VALUES(46,'John','Smith','','','2026-03-06T10:27:35',NULL,1,0,1);
INSERT INTO employees VALUES(47,'John','Smith','john.smith@company.com','','2026-03-06T10:27:45',NULL,0,10,1);
INSERT INTO employees VALUES(48,'John','Smith','','','2026-03-06T10:28:29',NULL,1,1,1);
INSERT INTO employees VALUES(49,'John','Smith','john.smith@company.com','','2026-03-06T10:28:50',NULL,0,10,1);
CREATE TABLE admins (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    job_title TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT
);
INSERT INTO admins VALUES(1,'Senior Administrator');
INSERT INTO admins VALUES(2,'Senior Administrator');
INSERT INTO admins VALUES(3,'Senior Administrator');
INSERT INTO admins VALUES(4,'Senior Administrator');
INSERT INTO admins VALUES(5,'Senior Administrator');
INSERT INTO admins VALUES(6,'Senior Administrator');
INSERT INTO admins VALUES(7,'Senior Administrator');
INSERT INTO admins VALUES(13,'Senior Administrator');
INSERT INTO admins VALUES(14,'Senior Administrator');
INSERT INTO admins VALUES(15,'Senior Administrator');
INSERT INTO admins VALUES(16,'Senior Administrator');
INSERT INTO admins VALUES(17,'System Administrator');
INSERT INTO admins VALUES(18,'System Administrator');
INSERT INTO admins VALUES(20,'System Administrator');
INSERT INTO admins VALUES(21,'System Administrator');
INSERT INTO admins VALUES(22,'System Administrator');
INSERT INTO admins VALUES(23,'System Administrator');
INSERT INTO admins VALUES(24,'System Administrator');
INSERT INTO admins VALUES(25,'System Administrator');
INSERT INTO admins VALUES(26,'System Administrator');
INSERT INTO admins VALUES(27,'System Administrator');
INSERT INTO admins VALUES(28,'System Administrator');
INSERT INTO admins VALUES(29,'System Administrator');
INSERT INTO admins VALUES(30,'System Administrator');
INSERT INTO admins VALUES(31,'System Administrator');
INSERT INTO admins VALUES(32,'System Administrator');
INSERT INTO admins VALUES(33,'System Administrator');
INSERT INTO admins VALUES(34,'System Administrator');
INSERT INTO admins VALUES(35,'System Administrator');
INSERT INTO admins VALUES(36,'System Administrator');
INSERT INTO admins VALUES(37,'System Administrator');
INSERT INTO admins VALUES(38,'System Administrator');
INSERT INTO admins VALUES(39,'Senior Administrator');
INSERT INTO admins VALUES(40,'Senior Administrator');
INSERT INTO admins VALUES(41,'System Administrator');
INSERT INTO admins VALUES(42,'Senior Administrator');
INSERT INTO admins VALUES(43,'Senior Administrator');
INSERT INTO admins VALUES(44,'System Administrator');
INSERT INTO admins VALUES(45,'Senior Administrator');
INSERT INTO admins VALUES(46,'System Administrator');
INSERT INTO admins VALUES(47,'Senior Administrator');
INSERT INTO admins VALUES(48,'System Administrator');
INSERT INTO admins VALUES(49,'Senior Administrator');
CREATE TABLE users (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
);
INSERT INTO users VALUES(8,1);
INSERT INTO users VALUES(9,1);
INSERT INTO users VALUES(10,1);
INSERT INTO users VALUES(11,1);
INSERT INTO users VALUES(12,1);
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	login TEXT,
	password TEXT,
	enabled INTEGER DEFAULT (1),
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
CREATE TABLE clients (
	client_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	name TEXT,
	address TEXT,
	email TEXT,
	phone TEXT,
	enabled INTEGER, version INTEGER,
	date_created TEXT,
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO clients VALUES(1,1,'name',NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER);
INSERT INTO roles VALUES(1,'name',NULL,NULL,NULL,NULL,1,NULL);
INSERT INTO roles VALUES(2,'name1',NULL,NULL,NULL,NULL,1,NULL);
CREATE TABLE admins_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO admins_roles VALUES(4,1);
INSERT INTO admins_roles VALUES(3,1);
INSERT INTO admins_roles VALUES(5,1);
INSERT INTO admins_roles VALUES(6,1);
INSERT INTO admins_roles VALUES(7,1);
INSERT INTO admins_roles VALUES(13,1);
INSERT INTO admins_roles VALUES(14,1);
INSERT INTO admins_roles VALUES(15,1);
INSERT INTO admins_roles VALUES(16,1);
INSERT INTO admins_roles VALUES(42,1);
INSERT INTO admins_roles VALUES(42,2);
INSERT INTO admins_roles VALUES(43,1);
INSERT INTO admins_roles VALUES(45,1);
INSERT INTO admins_roles VALUES(47,1);
INSERT INTO admins_roles VALUES(49,1);
CREATE TABLE users_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
CREATE TABLE tickets (
	ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- клиент
	admin_id INTEGER, -- создатель заявки
	user_id INTEGER DEFAULT(0), -- заявитель от клиента, может не быть
	user_ticket_contact_user_id INTEGER DEFAULT(0), -- контактное лицо от клиента. может не быть
	user_ticket_id INTEGER DEFAULT(0), -- связь с заявкой созданной пользователем клиентом, может не быть 
	text_of_ticket TEXT, -- текст заявки
	date_created TEXT, -- дата создания
	is_remote INTEGER DEFAULT (0), -- сделана удаленно, возможно удаленное решение
	is_closed INTEGER DEFAULT (0), -- заявка завершена
	date_closed TEXT, -- дата завершения или снятия заявки
	urgency_level INTEGER DEFAULT (0), -- срочная или несрочная 
	version INTEGER, -- версия
	CONSTRAINT tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT tickets_user_user_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES employees(employee_id) on delete restrict
);
CREATE TABLE tickets_comment (
	comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто оставил комментарий
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on DELETE restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict
);
CREATE TABLE tickets_executor_assignment (
	executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER, -- кто назначен
	ticket_id INTEGER,
	date_assignment TEXT,  
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete RESTRICT,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on DELETE restrict
);
CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто установил статус
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on DELETE restrict
);
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- заявки от какого клиента
	user_id INTEGER, -- кто создал заявку
	user_ticket_contact_user_id INTEGER DEFAULT(0), -- контактное лицо по заявке, может не быть
	text_of_ticket TEXT, -- текст заявки 
	date_created TEXT,
	version INTEGER, 
	date_closed TEXT, -- дата завершения или снятия заявки 
	is_closed INTEGER,
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES employees(employee_id) on delete restrict
);
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
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
CREATE TABLE user_tickets_executor_assignments (
	user_executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	admin_id INTEGER,
	date_assignment TEXT,
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',49);
INSERT INTO sqlite_sequence VALUES('accounts',119);
INSERT INTO sqlite_sequence VALUES('roles',2);
INSERT INTO sqlite_sequence VALUES('clients',3);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
COMMIT;

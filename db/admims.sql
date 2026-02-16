PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE employees (
	employee_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	firts_name TEXT,
	last_name TEXT,
	email TEXT,
	phone TEXT,
	date_created TEXT,
	address TEXT,
	enabled INTEGER DEFAULT (1),
	is_deleted INTEGER DEFAULT (0),
	version INTEGER
, is_admin INTEGER);
CREATE TABLE admins (
	admin_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	job_title TEXT
);
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	enabled INTEGER DEFAULT (1),
	login TEXT,
	password TEXT,
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
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
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
);
CREATE TABLE users (
	user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	client_id INTEGER,
	CONSTRAINT users_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
	CONSTRAINT users_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1)
, version INTEGER);
CREATE TABLE admins_roles (
	admin_role INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	role_id INTEGER,
	CONSTRAINT admins_roles_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id),
	CONSTRAINT admins_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
CREATE TABLE users_roles (
	user_role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	role_id INTEGER,
	user_id INTEGER,
	CONSTRAINT users_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id),
	CONSTRAINT users_roles_users_FK FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS "tickets_executor_assigments" (
	executor_assigment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	date_assigment TEXT,
	ticket_id INTEGER,
	CONSTRAINT executor_assigments_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id),
	CONSTRAINT executor_assigments_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);
CREATE TABLE IF NOT EXISTS "tickets_comment" (
	comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	comment TEXT,
	ticket_id INTEGER,
	admin_id INTEGER,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id),
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);
CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id)
);
CREATE TABLE tickets (
	ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER,
	admin_id INTEGER,
	description TEXT,
	text_of_ticket TEXT,
	date_created TEXT,
	is_remote INTEGER DEFAULT (0),
	is_finished INTEGER DEFAULT (0),
	date_finished INTEGER,
	vesrion INTEGER,
	urgency_level INTEGER,
	user_id INTEGER,
	CONSTRAINT tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id),
	CONSTRAINT tickets_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id),
	CONSTRAINT tickets_employees_user_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id)
);
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER,
	user_id INTEGER,
	description TEXT,
	date_created TEXT,
	version INTEGER,
	date_finished TEXT,
	is_closed INTEGER,
	promoted_ticket_id INTEGER,
	CONSTRAINT user_tickets_employees_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id),
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id),
	CONSTRAINT user_tickets_tickets_FK FOREIGN KEY (promoted_ticket_id) REFERENCES tickets(ticket_id)
);
CREATE TABLE IF NOT EXISTS "user_tickets_comment" (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	comment TEXT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id)
);
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id),
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
CREATE TABLE IF NOT EXISTS "uset_tickets_executor_assigments" (
	user_executor_assigment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	date_assigment TEXT,
	user_ticket_id INTEGER,
	CONSTRAINT executor_assigments_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id),
	CONSTRAINT executor_assigments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id)
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',1);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
COMMIT;

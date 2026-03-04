PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
-- 	блок для пользователей системы, admin и user начало
-- 	Таблица общих данных для admin и user
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

-- 	аdmin дополнительные данные
CREATE TABLE admins (
	admin_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	job_title TEXT,
	CONSTRAINT employee_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);

--	user дополнительные данные
CREATE TABLE users (
	user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	client_id INTEGER,
	CONSTRAINT users_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT users_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on DELETE restrict
);

--	account данные общие для admin и user
CREATE TABLE accounts (
	account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	login TEXT,
	password TEXT,
	enabled INTEGER DEFAULT (1),
	date_created TEXT,
	CONSTRAINT accounts_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);

-- client основные данные
CREATE TABLE clients (
	client_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	name TEXT,
	address TEXT,
	email TEXT,
	phone TEXT,
	enabled INTEGER, version INTEGER,
	date_created INTEGER,
	CONSTRAINT clients_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict
);



--блок для пользователей системы, admin и user начало конец

-- блок для RBAC начало
-- role основные данные ролей, permissions описаны в программе, здесь только их названия
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER);

-- admin role связывает admin и назначенные ему роли, многие ко многим
CREATE TABLE admins_roles (
	admin_role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER,
	role_id INTEGER,
	CONSTRAINT admins_roles_admins_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict,
	CONSTRAINT admins_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id) on DELETE restrict
);
-- user role связывает user и назначенные ему роли, многие ко многим
CREATE TABLE users_roles (
	user_role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	role_id INTEGER,
	user_id INTEGER,
	CONSTRAINT users_roles_roles_FK FOREIGN KEY (role_id) REFERENCES roles(role_id) on delete restrict,
	CONSTRAINT users_roles_users_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict
);
-- блок для RBAC конец


-- блок заявок начало
-- заявки от admin начало
-- ticket заявки от admin
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
	CONSTRAINT tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict,
	CONSTRAINT tickets_user_user_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES users(user_id) on delete restrict
);

-- комментарии для ticket
CREATE TABLE tickets_comment (
	comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто оставил комментарий
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict
);

-- назначенные исполнители
CREATE TABLE tickets_executor_assignment (
	executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER, -- кто назначен
	ticket_id INTEGER,
	date_assignment TEXT,  
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete RESTRICT,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on DELETE restrict
);

-- статусы заявок, сами статусы описаны в программе, здесь хранятся только строки
CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто установил статус
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on DELETE restrict
);
-- заявки от admin окончание

-- заявки созданные user 
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
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES users(user_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES users(user_id) on delete restrict
);

-- комментарии к заявке пользователя, могут оставлять как user так и admin
CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);


-- статусы заявок, сами статусы описаны в программе, здесь хранятся только строки, могут менять как admin так и user
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);

-- назначенный исполнитель
CREATE TABLE user_tickets_executor_assignments (
	user_executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	admin_id INTEGER,
	date_assignment TEXT,
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES admins(admin_id) on delete restrict,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);

CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
COMMIT;


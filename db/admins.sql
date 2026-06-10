PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE departments (
    department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    version INTEGER DEFAULT 0,
    date_created TEXT
);
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
INSERT INTO employees VALUES(4,'John','Smith','john.smith@company.com','','2026-03-05T11:29:33',NULL,1,7,1);
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
INSERT INTO employees VALUES(50,'John','Smith','','','1772821643',NULL,1,1,0);
INSERT INTO employees VALUES(51,'John','Smith','','','1772821778',NULL,1,0,0);
INSERT INTO employees VALUES(52,'John','Smith','','','1772821832',NULL,1,1,0);
INSERT INTO employees VALUES(53,'John','Smith','john.smith@company.com','','1772821887',NULL,1,2,0);
INSERT INTO employees VALUES(54,'John','Smith','','','2026-03-06T21:34:53',NULL,1,1,1);
INSERT INTO employees VALUES(55,'John','Smith','','','2026-03-06T21:38:43',NULL,1,0,1);
INSERT INTO employees VALUES(56,'John','Smith','','','2026-03-06T21:39:15',NULL,1,1,1);
INSERT INTO employees VALUES(57,'John','Smith','','','2026-03-06T22:05:42',NULL,1,0,1);
INSERT INTO employees VALUES(58,'John','Smith','john.smith@company.com','','2026-03-06T22:05:59',NULL,0,10,1);
INSERT INTO employees VALUES(59,'John','Smith','john.smith@company.com','','2026-03-06T22:06:11',NULL,0,10,1);
INSERT INTO employees VALUES(60,'John','Smith','john.smith@company.com','','1772823975',NULL,1,3,0);
INSERT INTO employees VALUES(61,'John','Smith','john.smith@company.com','','1772824012',NULL,0,7,0);
INSERT INTO employees VALUES(62,'John','Smith','john.smith@company.com','','1772824274',NULL,0,7,0);
INSERT INTO employees VALUES(63,'John','Smith','john.smith@company.com','','1772824279',NULL,0,7,0);
INSERT INTO employees VALUES(64,'John','Smith','john.smith@company.com','','1772824287',NULL,0,7,0);
INSERT INTO employees VALUES(65,'John','Smith','john.smith@company.com','','1772824330',NULL,1,5,0);
INSERT INTO employees VALUES(66,'John','Smith','','','2026-03-07T12:36:47',NULL,1,1,1);
INSERT INTO employees VALUES(67,'Alice','Brown','','','1772876207',NULL,1,0,0);
INSERT INTO employees VALUES(68,'John','Smith','','','2026-03-07T12:50:39',NULL,1,1,1);
INSERT INTO employees VALUES(69,'Alice','Brown','','','1772877039',NULL,1,0,0);
INSERT INTO employees VALUES(70,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:23:22',NULL,1,5,1);
INSERT INTO employees VALUES(71,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:23:52',NULL,1,5,1);
INSERT INTO employees VALUES(72,'John','Smith','11@11.fgerg','12345','2026-03-30T17:23:52',NULL,1,4,1);
INSERT INTO employees VALUES(73,'John','Smith','11@11.fgerg','12345','2026-03-30T17:23:52',NULL,1,4,1);
INSERT INTO employees VALUES(74,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:24:37',NULL,1,5,1);
INSERT INTO employees VALUES(75,'John','Smith','11@11.fgerg','12345','2026-03-30T17:24:38',NULL,1,4,1);
INSERT INTO employees VALUES(76,'John','Smith','11@11.fgerg','12345','2026-03-30T17:24:38',NULL,1,5,1);
INSERT INTO employees VALUES(77,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:24:50',NULL,1,5,1);
INSERT INTO employees VALUES(78,'John','Smith','11@11.fgerg','12345','2026-03-30T17:24:50',NULL,1,4,1);
INSERT INTO employees VALUES(79,'John','Smith','11@11.fgerg','12345','2026-03-30T17:24:50',NULL,1,5,1);
INSERT INTO employees VALUES(80,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:25:32',NULL,1,5,1);
INSERT INTO employees VALUES(81,'John','Smith','11@11.fgerg','12345','2026-03-30T17:25:32',NULL,1,4,1);
INSERT INTO employees VALUES(82,'John','Smith','11@11.fgerg','12345','2026-03-30T17:25:32',NULL,1,5,1);
INSERT INTO employees VALUES(83,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:26:54',NULL,1,5,1);
INSERT INTO employees VALUES(84,'John','Smith','11@11.fgerg','12345','2026-03-30T17:26:54',NULL,1,4,1);
INSERT INTO employees VALUES(85,'John','Smith','11@11.fgerg','12345','2026-03-30T17:26:54',NULL,1,5,1);
INSERT INTO employees VALUES(86,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:27:30',NULL,1,5,1);
INSERT INTO employees VALUES(87,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:30',NULL,1,4,1);
INSERT INTO employees VALUES(88,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:30',NULL,1,5,1);
INSERT INTO employees VALUES(89,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:27:39',NULL,1,5,1);
INSERT INTO employees VALUES(90,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:39',NULL,1,4,1);
INSERT INTO employees VALUES(91,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:39',NULL,1,5,1);
INSERT INTO employees VALUES(92,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:27:53',NULL,1,5,1);
INSERT INTO employees VALUES(93,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:53',NULL,1,4,1);
INSERT INTO employees VALUES(94,'John','Smith','11@11.fgerg','12345','2026-03-30T17:27:53',NULL,1,5,1);
INSERT INTO employees VALUES(95,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:28:31',NULL,1,5,1);
INSERT INTO employees VALUES(96,'John','Smith','11@11.fgerg','12345','2026-03-30T17:28:31',NULL,1,4,1);
INSERT INTO employees VALUES(97,'John','Smith','11@11.fgerg','12345','2026-03-30T17:28:31',NULL,1,5,1);
INSERT INTO employees VALUES(98,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:30:24',NULL,1,5,1);
INSERT INTO employees VALUES(99,'John','Smith','11@11.fgerg','12345','2026-03-30T17:30:24',NULL,1,4,1);
INSERT INTO employees VALUES(100,'John','Smith','11@11.fgerg','12345','2026-03-30T17:30:24',NULL,1,5,1);
INSERT INTO employees VALUES(101,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:31:56',NULL,1,5,1);
INSERT INTO employees VALUES(102,'John','Smith','11@11.fgerg','12345','2026-03-30T17:31:56',NULL,1,4,1);
INSERT INTO employees VALUES(103,'John','Smith','11@11.fgerg','12345','2026-03-30T17:31:56',NULL,1,5,1);
INSERT INTO employees VALUES(104,'first name1','Smith','11@11.fgerg','12345','2026-03-30T17:33:58',NULL,1,5,1);
INSERT INTO employees VALUES(105,'John','Smith','11@11.fgerg','12345','2026-03-30T17:33:58',NULL,1,4,1);
INSERT INTO employees VALUES(106,'John','Smith','11@11.fgerg','12345','2026-03-30T17:33:58',NULL,1,5,1);
INSERT INTO employees VALUES(107,'John','Smith','11@11.fgerg','12345','2026-03-30T18:33:38',NULL,1,1,0);
INSERT INTO employees VALUES(108,'John','Smith','11@11.fgerg','12345','2026-03-30T18:41:52',NULL,1,1,0);
INSERT INTO employees VALUES(109,'John','Smith','11@11.fgerg','12345','2026-03-30T18:41:56',NULL,1,1,0);
INSERT INTO employees VALUES(110,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:30:48',NULL,1,4,1);
INSERT INTO employees VALUES(111,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:31:35',NULL,1,5,1);
INSERT INTO employees VALUES(112,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:31:55',NULL,1,5,1);
INSERT INTO employees VALUES(113,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:32:00',NULL,1,8,1);
INSERT INTO employees VALUES(114,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:32:01',NULL,1,8,1);
INSERT INTO employees VALUES(115,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:32:09',NULL,1,8,1);
INSERT INTO employees VALUES(116,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:33:09',NULL,1,4,1);
INSERT INTO employees VALUES(117,'John','Johnson','john.johnson@example.com','+1 555 999 0000','2026-04-07T15:33:22',NULL,1,4,1);
INSERT INTO employees VALUES(118,'John','Smith','john.smith@example.com','+1 555 123 4567','2026-04-07T15:34:39',NULL,1,2,1);
INSERT INTO employees VALUES(119,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-14T18:13:46',NULL,1,2,1);
INSERT INTO employees VALUES(120,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19T13:15:25',NULL,1,2,1);
INSERT INTO employees VALUES(121,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19T13:26:56',NULL,1,2,1);
INSERT INTO employees VALUES(122,'Alice','Brown','alice.brown@example.com','+1 555 100 9999','2026-05-19T13:29:27',NULL,1,3,1);
INSERT INTO employees VALUES(123,'Bob','Smith','bob.smith@example.com','+1 555 222 3333','2026-05-19T13:47:54',NULL,1,1,0);
INSERT INTO employees VALUES(124,'Bob','Johnson','bob.johnson@example.com','+1 555 222 9999','2026-05-19T13:48:41',NULL,1,2,0);
INSERT INTO employees VALUES(125,'Bob','Johnson','bob.johnson@example.com','+1 555 222 9999','2026-05-19T13:49:00',NULL,1,4,0);
INSERT INTO employees VALUES(126,'Bob','Smith','bob.smith@example.com','+1 555 222 3333','2026-05-19T14:47:51',NULL,1,1,0);
INSERT INTO employees VALUES(127,'Bob','Johnson','bob.johnson@example.com','+1 555 222 9999','2026-05-19T14:54:52',NULL,0,4,0);
INSERT INTO employees VALUES(128,'string','','','','2026-05-28T15:01:24',NULL,1,1,1);
INSERT INTO employees VALUES(129,'string1','','','','2026-05-28T15:02:07',NULL,1,1,1);
INSERT INTO employees VALUES(130,'string2','','','','2026-05-28T15:02:45',NULL,1,1,1);
INSERT INTO employees VALUES(131,'string','фамилия','11@11.ru','телефон','2026-06-01T14:53:50',NULL,1,1,1);
INSERT INTO employees VALUES(132,'string','фамилия','11@11.ru','телефон','2026-06-01T15:37:45',NULL,1,1,1);
INSERT INTO employees VALUES(133,'string','фамилия','','телефон','2026-06-01T15:43:01',NULL,1,1,1);
INSERT INTO employees VALUES(134,'string','фамилия','','телефон','2026-06-01T15:43:17',NULL,1,1,1);
INSERT INTO employees VALUES(135,'string','фамилия','','телефон','2026-06-01T15:43:34',NULL,1,1,1);
INSERT INTO employees VALUES(136,'string','фамилия','','телефон','2026-06-01T15:45:39',NULL,1,1,1);
INSERT INTO employees VALUES(137,'string','фамилия','','телефон','2026-06-01T15:45:56',NULL,1,1,1);
INSERT INTO employees VALUES(138,'name1','efwerfwerf','','','2026-06-01T15:48:13',NULL,1,16,1);
INSERT INTO employees VALUES(139,'string','','','телефон','2026-06-01T15:54:13',NULL,1,1,1);
INSERT INTO employees VALUES(140,'string','','','','2026-06-01T17:20:06',NULL,1,1,0);
INSERT INTO employees VALUES(141,'string','','','','2026-06-01T17:21:49',NULL,1,1,0);
INSERT INTO employees VALUES(142,'string','','','','2026-06-01T17:24:48',NULL,1,1,0);
INSERT INTO employees VALUES(143,'efwfrwferfergfer','ferferferfg','','','2026-06-04T14:18:52',NULL,1,4,1);
INSERT INTO employees VALUES(144,'string','','','','2026-06-04T14:21:57',NULL,1,0,0);
INSERT INTO employees VALUES(145,'string','6uy56u6yu56u56uy56u','','','2026-06-04T15:10:58',NULL,1,1,1);
INSERT INTO employees VALUES(146,'string','6uy56u6yu56u56uy56u','','','2026-06-04T15:11:31',NULL,0,3,1);
INSERT INTO employees VALUES(147,'string','6uy56u6yu56u56uy56u','','','2026-06-04T16:00:02',NULL,1,1,1);
INSERT INTO employees VALUES(148,'string','','','','2026-06-04T16:01:58',NULL,1,1,1);
INSERT INTO employees VALUES(149,'name','','','','2026-06-04T16:26:28',NULL,1,5,1);
INSERT INTO employees VALUES(150,'name','','','','2026-06-04T16:36:06',NULL,1,3,1);
INSERT INTO employees VALUES(151,'string','','','','2026-06-08T12:54:37',NULL,1,1,1);
INSERT INTO employees VALUES(152,'string','','','','2026-06-08T12:54:50',NULL,1,1,1);
INSERT INTO employees VALUES(153,'string','','','','2026-06-08T12:56:13',NULL,1,1,1);
INSERT INTO employees VALUES(154,'string','','','','2026-06-08T13:48:41',NULL,1,1,1);
INSERT INTO employees VALUES(156,'string','','','','2026-06-08T13:58:49',NULL,1,0,1);
INSERT INTO employees VALUES(157,'string','','','','2026-06-08T13:59:33',NULL,1,0,1);
INSERT INTO employees VALUES(158,'string','','','','2026-06-08T14:00:46',NULL,1,0,1);
INSERT INTO employees VALUES(159,'string','','','','2026-06-08T14:03:49',NULL,1,0,1);
INSERT INTO employees VALUES(160,'string','','','','2026-06-08T17:39:36',NULL,1,2,1);
INSERT INTO employees VALUES(161,'string','','','','2026-06-08T17:42:23',NULL,1,1,1);
INSERT INTO employees VALUES(162,'string','','','','2026-06-08T17:43:00',NULL,1,0,0);
INSERT INTO employees VALUES(163,'string','','','','2026-06-08T18:10:58',NULL,1,0,0);
INSERT INTO employees VALUES(164,'string','','','','2026-06-08T18:11:46',NULL,1,5,0);
INSERT INTO employees VALUES(165,'string','','','','2026-06-09T13:27:00',NULL,1,1,0);
INSERT INTO employees VALUES(166,'string','','','','2026-06-09T13:32:06',NULL,1,1,0);
INSERT INTO employees VALUES(167,'string','','','','2026-06-09T13:34:55',NULL,1,1,0);
INSERT INTO employees VALUES(168,'string','','','','2026-06-09T13:35:41',NULL,1,0,1);
INSERT INTO employees VALUES(169,'string','','','','2026-06-09T13:36:08',NULL,1,1,1);
INSERT INTO employees VALUES(170,'string','','','','2026-06-09T17:28:30',NULL,1,0,1);
INSERT INTO employees VALUES(171,'new2','','','','2026-06-09T17:29:33',NULL,1,9,1);
INSERT INTO employees VALUES(172,'n2','','','','2026-06-09T17:38:04',NULL,1,8,0);
CREATE TABLE admins (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    job_title TEXT, 
    department_id INTEGER DEFAULT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
INSERT INTO admins VALUES(1,'Senior Administrator',NULL);
INSERT INTO admins VALUES(2,'Senior Administrator',NULL);
INSERT INTO admins VALUES(3,'Senior Administrator',NULL);
INSERT INTO admins VALUES(4,'Senior Administrator',NULL);
INSERT INTO admins VALUES(5,'Senior Administrator',NULL);
INSERT INTO admins VALUES(6,'Senior Administrator',NULL);
INSERT INTO admins VALUES(7,'Senior Administrator',NULL);
INSERT INTO admins VALUES(13,'Senior Administrator',NULL);
INSERT INTO admins VALUES(14,'Senior Administrator',NULL);
INSERT INTO admins VALUES(15,'Senior Administrator',NULL);
INSERT INTO admins VALUES(16,'Senior Administrator',NULL);
INSERT INTO admins VALUES(17,'System Administrator',NULL);
INSERT INTO admins VALUES(18,'System Administrator',NULL);
INSERT INTO admins VALUES(20,'System Administrator',NULL);
INSERT INTO admins VALUES(21,'System Administrator',NULL);
INSERT INTO admins VALUES(22,'System Administrator',NULL);
INSERT INTO admins VALUES(23,'System Administrator',NULL);
INSERT INTO admins VALUES(24,'System Administrator',NULL);
INSERT INTO admins VALUES(25,'System Administrator',NULL);
INSERT INTO admins VALUES(26,'System Administrator',NULL);
INSERT INTO admins VALUES(27,'System Administrator',NULL);
INSERT INTO admins VALUES(28,'System Administrator',NULL);
INSERT INTO admins VALUES(29,'System Administrator',NULL);
INSERT INTO admins VALUES(30,'System Administrator',NULL);
INSERT INTO admins VALUES(31,'System Administrator',NULL);
INSERT INTO admins VALUES(32,'System Administrator',NULL);
INSERT INTO admins VALUES(33,'System Administrator',NULL);
INSERT INTO admins VALUES(34,'System Administrator',NULL);
INSERT INTO admins VALUES(35,'System Administrator',NULL);
INSERT INTO admins VALUES(36,'System Administrator',NULL);
INSERT INTO admins VALUES(37,'System Administrator',NULL);
INSERT INTO admins VALUES(38,'System Administrator',NULL);
INSERT INTO admins VALUES(39,'Senior Administrator',NULL);
INSERT INTO admins VALUES(40,'Senior Administrator',NULL);
INSERT INTO admins VALUES(41,'System Administrator',NULL);
INSERT INTO admins VALUES(42,'Senior Administrator',NULL);
INSERT INTO admins VALUES(43,'Senior Administrator',NULL);
INSERT INTO admins VALUES(44,'System Administrator',NULL);
INSERT INTO admins VALUES(45,'Senior Administrator',NULL);
INSERT INTO admins VALUES(46,'System Administrator',NULL);
INSERT INTO admins VALUES(47,'Senior Administrator',NULL);
INSERT INTO admins VALUES(48,'System Administrator',NULL);
INSERT INTO admins VALUES(49,'Senior Administrator',NULL);
INSERT INTO admins VALUES(54,'System Administrator',NULL);
INSERT INTO admins VALUES(55,'System Administrator',NULL);
INSERT INTO admins VALUES(56,'System Administrator',NULL);
INSERT INTO admins VALUES(57,'System Administrator',NULL);
INSERT INTO admins VALUES(58,'Senior Administrator',NULL);
INSERT INTO admins VALUES(59,'Senior Administrator',NULL);
INSERT INTO admins VALUES(66,'System Administrator',NULL);
INSERT INTO admins VALUES(68,'System Administrator',NULL);
INSERT INTO admins VALUES(70,'',NULL);
INSERT INTO admins VALUES(71,'',NULL);
INSERT INTO admins VALUES(72,'',NULL);
INSERT INTO admins VALUES(73,'',NULL);
INSERT INTO admins VALUES(74,'',NULL);
INSERT INTO admins VALUES(75,'',NULL);
INSERT INTO admins VALUES(76,'',NULL);
INSERT INTO admins VALUES(77,'',NULL);
INSERT INTO admins VALUES(78,'',NULL);
INSERT INTO admins VALUES(79,'',NULL);
INSERT INTO admins VALUES(80,'',NULL);
INSERT INTO admins VALUES(81,'',NULL);
INSERT INTO admins VALUES(82,'',NULL);
INSERT INTO admins VALUES(83,'',NULL);
INSERT INTO admins VALUES(84,'',NULL);
INSERT INTO admins VALUES(85,'',NULL);
INSERT INTO admins VALUES(86,'',NULL);
INSERT INTO admins VALUES(87,'',NULL);
INSERT INTO admins VALUES(88,'',NULL);
INSERT INTO admins VALUES(89,'',NULL);
INSERT INTO admins VALUES(90,'',NULL);
INSERT INTO admins VALUES(91,'',NULL);
INSERT INTO admins VALUES(92,'',NULL);
INSERT INTO admins VALUES(93,'',NULL);
INSERT INTO admins VALUES(94,'',NULL);
INSERT INTO admins VALUES(95,'',NULL);
INSERT INTO admins VALUES(96,'',NULL);
INSERT INTO admins VALUES(97,'',NULL);
INSERT INTO admins VALUES(98,'',NULL);
INSERT INTO admins VALUES(99,'',NULL);
INSERT INTO admins VALUES(100,'',NULL);
INSERT INTO admins VALUES(101,'',NULL);
INSERT INTO admins VALUES(102,'',NULL);
INSERT INTO admins VALUES(103,'',NULL);
INSERT INTO admins VALUES(104,'',NULL);
INSERT INTO admins VALUES(105,'',NULL);
INSERT INTO admins VALUES(106,'',NULL);
INSERT INTO admins VALUES(110,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(111,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(112,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(113,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(114,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(115,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(116,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(117,'Senior System Administrator',NULL);
INSERT INTO admins VALUES(118,'System Administrator',NULL);
INSERT INTO admins VALUES(119,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(120,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(121,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(122,'Senior Operations Manager',NULL);
INSERT INTO admins VALUES(128,'job title',NULL);
INSERT INTO admins VALUES(129,'job title',NULL);
INSERT INTO admins VALUES(130,'',NULL);
INSERT INTO admins VALUES(131,'админ',NULL);
INSERT INTO admins VALUES(132,'админ',NULL);
INSERT INTO admins VALUES(133,'админ',NULL);
INSERT INTO admins VALUES(134,'админ',NULL);
INSERT INTO admins VALUES(135,'админ',NULL);
INSERT INTO admins VALUES(136,'админ',NULL);
INSERT INTO admins VALUES(137,'админ',NULL);
INSERT INTO admins VALUES(138,'',NULL);
INSERT INTO admins VALUES(139,'админ',NULL);
INSERT INTO admins VALUES(143,'',NULL);
INSERT INTO admins VALUES(145,'',NULL);
INSERT INTO admins VALUES(146,'',NULL);
INSERT INTO admins VALUES(147,'',NULL);
INSERT INTO admins VALUES(148,'',NULL);
INSERT INTO admins VALUES(149,'',NULL);
INSERT INTO admins VALUES(150,'',NULL);
INSERT INTO admins VALUES(151,'',NULL);
INSERT INTO admins VALUES(152,'',NULL);
INSERT INTO admins VALUES(153,'',NULL);
INSERT INTO admins VALUES(154,'',NULL);
INSERT INTO admins VALUES(156,'',NULL);
INSERT INTO admins VALUES(157,'',NULL);
INSERT INTO admins VALUES(158,'',NULL);
INSERT INTO admins VALUES(159,'',NULL);
INSERT INTO admins VALUES(160,'',NULL);
INSERT INTO admins VALUES(161,'',NULL);
INSERT INTO admins VALUES(168,'',NULL);
INSERT INTO admins VALUES(169,'',NULL);
INSERT INTO admins VALUES(170,'',NULL);
INSERT INTO admins VALUES(171,'',NULL);
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
INSERT INTO users VALUES(50,1);
INSERT INTO users VALUES(51,1);
INSERT INTO users VALUES(52,1);
INSERT INTO users VALUES(53,1);
INSERT INTO users VALUES(60,1);
INSERT INTO users VALUES(61,1);
INSERT INTO users VALUES(62,1);
INSERT INTO users VALUES(63,1);
INSERT INTO users VALUES(64,1);
INSERT INTO users VALUES(65,1);
INSERT INTO users VALUES(67,4);
INSERT INTO users VALUES(69,5);
INSERT INTO users VALUES(107,1);
INSERT INTO users VALUES(108,1);
INSERT INTO users VALUES(109,1);
INSERT INTO users VALUES(123,4);
INSERT INTO users VALUES(124,4);
INSERT INTO users VALUES(125,4);
INSERT INTO users VALUES(126,4);
INSERT INTO users VALUES(127,4);
INSERT INTO users VALUES(140,4);
INSERT INTO users VALUES(141,4);
INSERT INTO users VALUES(142,4);
INSERT INTO users VALUES(144,4);
INSERT INTO users VALUES(162,4);
INSERT INTO users VALUES(163,4);
INSERT INTO users VALUES(164,4);
INSERT INTO users VALUES(165,4);
INSERT INTO users VALUES(166,4);
INSERT INTO users VALUES(167,4);
INSERT INTO users VALUES(172,4);
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
INSERT INTO accounts VALUES(406,122,'alice.johnson20260519132927','1a6570efcd82a670697bb2d2e0bef083b1a0ce20b916f1d0336994f1aa70a336',1,'2026-05-19T13:29:27');
INSERT INTO accounts VALUES(410,123,'bob.smith20260519134754','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'1779187674');
INSERT INTO accounts VALUES(412,124,'bob.smith20260519134841','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'1779187721');
INSERT INTO accounts VALUES(415,125,'bob','6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',1,'1779187740');
INSERT INTO accounts VALUES(420,126,'bob.smith20260519144710','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',1,'1779191271');
INSERT INTO accounts VALUES(422,127,'bob.smith20260519145452','805bd951772627f3d1a607084df1727c6caad60447c5d73febf7be2d2fe17fd8',0,'2026-05-19T14:54:52');
INSERT INTO accounts VALUES(427,128,'login','e5c423e29a981dd8149066bebe675f3979fb9c7f1cbe97db92604ccbbeba4493',1,'2026-05-28T15:01:24');
INSERT INTO accounts VALUES(429,131,'login-string','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T14:53:50');
INSERT INTO accounts VALUES(431,132,'login-string1','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T15:37:45');
INSERT INTO accounts VALUES(433,133,'login-string11','57fe565614d67b08165f8f9864f04d9edb220bbde21356bc59cca015d94a9ef5',1,'2026-06-01T15:43:01');
INSERT INTO accounts VALUES(435,137,'логин','1bd627127cd59de4669ce89386e2180cd63f61af5b59045329545a2f197c981b',1,'2026-06-01T15:45:56');
INSERT INTO accounts VALUES(441,138,'string1111111111111111112111111111111','5797a9aba74864f5f0876523d4e63dd83298be2fe3c50eb4711cbb981ddb200f',1,'2026-06-01T17:11:09');
INSERT INTO accounts VALUES(447,142,'login-user','1bd627127cd59de4669ce89386e2180cd63f61af5b59045329545a2f197c981b',1,'2026-06-01T17:24:48');
INSERT INTO accounts VALUES(455,147,'login-new1010','409d93026fcb52ae62a8d9c892f49054a3718eca11ce14e87a95b2ec06f4e509',1,'2026-06-04T16:00:02');
INSERT INTO accounts VALUES(466,160,'login10','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-08T17:39:36');
INSERT INTO accounts VALUES(468,161,'login11','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-08T17:42:23');
INSERT INTO accounts VALUES(471,164,'string-login','e530f300120d9ba00f9d79b092aadd36ab4c2bfb96a6a995e8a479fdc2b0726f',1,'2026-06-08T18:11:46');
INSERT INTO accounts VALUES(472,166,'login-u','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:32:06');
INSERT INTO accounts VALUES(474,167,'login-user1','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:34:48');
INSERT INTO accounts VALUES(476,168,'login-admin','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:35:41');
INSERT INTO accounts VALUES(477,169,'login-admin1','d85fb61a933e0b8a45f88c89888502573a3d318657a576ef5529bf948b98882c',1,'2026-06-09T13:36:45');
INSERT INTO accounts VALUES(483,170,'htyhyrujujuj','ff7bd97b1a7789ddd2775122fd6817f3173672da9f802ceec57f284325bf589f',1,'2026-06-09T17:28:30');
INSERT INTO accounts VALUES(485,172,'erfertgrtg','ff7bd97b1a7789ddd2775122fd6817f3173672da9f802ceec57f284325bf589f',1,'2026-06-09T17:38:04');
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
INSERT INTO clients VALUES(4,66,'ACME Corporation','','','',1,0,'2026-03-07T12:36:47.340385');
INSERT INTO clients VALUES(5,68,'ACME Corporation','','','',1,0,'2026-03-07T12:50:39.051346');
INSERT INTO clients VALUES(6,122,'string','','','',1,1,'2026-05-19T13:37:57.791729');
INSERT INTO clients VALUES(7,122,'string','','','',1,1,'2026-05-25T15:32:53.042860');
INSERT INTO clients VALUES(8,122,'string','','','',1,1,'2026-05-25T15:36:48.340639');
INSERT INTO clients VALUES(9,122,'string','','','',1,1,'2026-05-25T15:45:07.015557');
INSERT INTO clients VALUES(10,122,'string','','','',1,1,'2026-05-25T15:50:46.624171');
INSERT INTO clients VALUES(11,122,'string','efrwghetghetget','','',1,1,'2026-05-25T15:51:05.464638');
INSERT INTO clients VALUES(12,122,'string','efrwghetghetget','','',1,1,'2026-05-25T16:02:53.736079');
INSERT INTO clients VALUES(13,122,'string','efrwghetghet111get','','',1,1,'2026-05-25T16:03:00.852692');
INSERT INTO clients VALUES(14,122,'str111ing','efrwghetghet111get','','',1,1,'2026-05-25T16:03:22.691814');
INSERT INTO clients VALUES(16,122,'werfrwfgwer','','efwerfwf@efwrfgerfg.ferfggetg','',1,1,'2026-05-25T17:05:00.155946');
INSERT INTO clients VALUES(17,122,'string','','','',1,6,'2026-05-27T16:09:12.272193');
INSERT INTO clients VALUES(19,122,'string','','111@1111.ru','',1,5,'2026-06-01T14:25:43.721135');
INSERT INTO clients VALUES(21,122,'string','dqeded','11@11.wdqedqe','',1,8,'2026-06-03T17:07:21.677730');
INSERT INTO clients VALUES(23,122,'string','','','',1,1,'2026-06-04T15:03:32.844573');
INSERT INTO clients VALUES(24,122,'string','','','',1,4,'2026-06-04T15:03:55.825620');
INSERT INTO clients VALUES(25,160,'string-клиент','','','',1,1,'2026-06-08T17:40:31.506929');
CREATE TABLE roles (
	role_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	permissions TEXT,
	description TEXT,
	is_system_role INTEGER,
	date_created TEXT,
	is_admin INTEGER DEFAULT (1), 
	version INTEGER);
INSERT INTO roles VALUES(5,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.view, role.assign, role.revoke','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(7,'Super Admin','admin.view,role.assign,audit.view,admin.update,role.revoke,create.user,ticket.create,create.admin','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(60,'Super Admin','client.operation, client.view, admin.operation, admin.view, user.operation, user.view, ticket.operation, ticket.view, role.assign, role.revoke','Full system access',1,'2026-03-23T12:21:42+00:00',1,0);
INSERT INTO roles VALUES(61,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:21:42+00:00',0,0);
INSERT INTO roles VALUES(62,'Super Admin','audit.view,role.assign,admin.view','Full system access',1,'2026-03-23T12:22:06+00:00',1,0);
INSERT INTO roles VALUES(63,'Ticket Creator','ticket.operation, ticket.operation.all, ticket.view, ticket.view.all','Can create and view own tickets',0,'2026-03-23T12:22:06+00:00',0,0);
INSERT INTO roles VALUES(64,'Super Admin','audit.view,role.assign,admin.view','Full system access',1,'2026-03-23T12:22:34+00:00',1,0);
INSERT INTO roles VALUES(65,'Ticket Creator','ticket.view.own,ticket.create','Can create and view own tickets',0,'2026-03-23T12:22:34+00:00',0,0);
INSERT INTO roles VALUES(66,'Super Admin','audit.view,role.assign,admin.view','Full system access',1,'2026-03-23T12:22:49+00:00',1,0);
CREATE TABLE admins_roles (
  employee_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (employee_id, role_id),
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
INSERT INTO admins_roles VALUES(4,60);
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
INSERT INTO admins_roles VALUES(58,1);
INSERT INTO admins_roles VALUES(59,1);
INSERT INTO admins_roles VALUES(66,1);
INSERT INTO admins_roles VALUES(68,1);
INSERT INTO admins_roles VALUES(70,60);
INSERT INTO admins_roles VALUES(70,62);
INSERT INTO admins_roles VALUES(71,60);
INSERT INTO admins_roles VALUES(71,62);
INSERT INTO admins_roles VALUES(72,60);
INSERT INTO admins_roles VALUES(72,62);
INSERT INTO admins_roles VALUES(73,60);
INSERT INTO admins_roles VALUES(73,62);
INSERT INTO admins_roles VALUES(74,60);
INSERT INTO admins_roles VALUES(74,62);
INSERT INTO admins_roles VALUES(75,60);
INSERT INTO admins_roles VALUES(75,62);
INSERT INTO admins_roles VALUES(76,62);
INSERT INTO admins_roles VALUES(77,60);
INSERT INTO admins_roles VALUES(77,62);
INSERT INTO admins_roles VALUES(78,60);
INSERT INTO admins_roles VALUES(78,62);
INSERT INTO admins_roles VALUES(79,62);
INSERT INTO admins_roles VALUES(80,60);
INSERT INTO admins_roles VALUES(80,62);
INSERT INTO admins_roles VALUES(81,60);
INSERT INTO admins_roles VALUES(81,62);
INSERT INTO admins_roles VALUES(82,62);
INSERT INTO admins_roles VALUES(83,60);
INSERT INTO admins_roles VALUES(83,62);
INSERT INTO admins_roles VALUES(84,60);
INSERT INTO admins_roles VALUES(84,62);
INSERT INTO admins_roles VALUES(85,62);
INSERT INTO admins_roles VALUES(86,60);
INSERT INTO admins_roles VALUES(86,62);
INSERT INTO admins_roles VALUES(87,60);
INSERT INTO admins_roles VALUES(87,62);
INSERT INTO admins_roles VALUES(88,62);
INSERT INTO admins_roles VALUES(89,60);
INSERT INTO admins_roles VALUES(89,62);
INSERT INTO admins_roles VALUES(90,60);
INSERT INTO admins_roles VALUES(90,62);
INSERT INTO admins_roles VALUES(91,62);
INSERT INTO admins_roles VALUES(92,60);
INSERT INTO admins_roles VALUES(92,62);
INSERT INTO admins_roles VALUES(93,60);
INSERT INTO admins_roles VALUES(93,62);
INSERT INTO admins_roles VALUES(94,62);
INSERT INTO admins_roles VALUES(95,60);
INSERT INTO admins_roles VALUES(95,62);
INSERT INTO admins_roles VALUES(96,60);
INSERT INTO admins_roles VALUES(96,62);
INSERT INTO admins_roles VALUES(97,62);
INSERT INTO admins_roles VALUES(98,60);
INSERT INTO admins_roles VALUES(98,62);
INSERT INTO admins_roles VALUES(99,60);
INSERT INTO admins_roles VALUES(99,62);
INSERT INTO admins_roles VALUES(100,62);
INSERT INTO admins_roles VALUES(101,60);
INSERT INTO admins_roles VALUES(101,62);
INSERT INTO admins_roles VALUES(102,60);
INSERT INTO admins_roles VALUES(102,62);
INSERT INTO admins_roles VALUES(103,62);
INSERT INTO admins_roles VALUES(104,60);
INSERT INTO admins_roles VALUES(104,62);
INSERT INTO admins_roles VALUES(105,60);
INSERT INTO admins_roles VALUES(105,62);
INSERT INTO admins_roles VALUES(106,62);
INSERT INTO admins_roles VALUES(110,60);
INSERT INTO admins_roles VALUES(110,62);
INSERT INTO admins_roles VALUES(111,66);
INSERT INTO admins_roles VALUES(111,60);
INSERT INTO admins_roles VALUES(111,62);
INSERT INTO admins_roles VALUES(112,66);
INSERT INTO admins_roles VALUES(112,60);
INSERT INTO admins_roles VALUES(112,62);
INSERT INTO admins_roles VALUES(113,66);
INSERT INTO admins_roles VALUES(113,62);
INSERT INTO admins_roles VALUES(114,66);
INSERT INTO admins_roles VALUES(114,62);
INSERT INTO admins_roles VALUES(115,66);
INSERT INTO admins_roles VALUES(115,62);
INSERT INTO admins_roles VALUES(116,60);
INSERT INTO admins_roles VALUES(116,62);
INSERT INTO admins_roles VALUES(117,60);
INSERT INTO admins_roles VALUES(117,62);
INSERT INTO admins_roles VALUES(118,60);
INSERT INTO admins_roles VALUES(118,62);
INSERT INTO admins_roles VALUES(1,60);
INSERT INTO admins_roles VALUES(119,5);
INSERT INTO admins_roles VALUES(119,7);
INSERT INTO admins_roles VALUES(120,5);
INSERT INTO admins_roles VALUES(120,7);
INSERT INTO admins_roles VALUES(121,5);
INSERT INTO admins_roles VALUES(121,7);
INSERT INTO admins_roles VALUES(122,5);
INSERT INTO admins_roles VALUES(128,64);
INSERT INTO admins_roles VALUES(129,64);
INSERT INTO admins_roles VALUES(130,64);
INSERT INTO admins_roles VALUES(131,64);
INSERT INTO admins_roles VALUES(131,66);
INSERT INTO admins_roles VALUES(132,64);
INSERT INTO admins_roles VALUES(132,66);
INSERT INTO admins_roles VALUES(133,64);
INSERT INTO admins_roles VALUES(133,66);
INSERT INTO admins_roles VALUES(134,64);
INSERT INTO admins_roles VALUES(134,66);
INSERT INTO admins_roles VALUES(135,64);
INSERT INTO admins_roles VALUES(135,66);
INSERT INTO admins_roles VALUES(136,64);
INSERT INTO admins_roles VALUES(136,66);
INSERT INTO admins_roles VALUES(137,64);
INSERT INTO admins_roles VALUES(137,66);
INSERT INTO admins_roles VALUES(139,64);
INSERT INTO admins_roles VALUES(138,66);
INSERT INTO admins_roles VALUES(143,5);
INSERT INTO admins_roles VALUES(145,5);
INSERT INTO admins_roles VALUES(146,5);
INSERT INTO admins_roles VALUES(147,5);
INSERT INTO admins_roles VALUES(148,5);
INSERT INTO admins_roles VALUES(149,5);
INSERT INTO admins_roles VALUES(150,5);
INSERT INTO admins_roles VALUES(151,5);
INSERT INTO admins_roles VALUES(152,5);
INSERT INTO admins_roles VALUES(153,5);
INSERT INTO admins_roles VALUES(154,5);
INSERT INTO admins_roles VALUES(161,60);
INSERT INTO admins_roles VALUES(161,5);
INSERT INTO admins_roles VALUES(160,5);
INSERT INTO admins_roles VALUES(171,5);
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
CREATE TABLE tickets_comment (
	comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто оставил комментарий
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on DELETE restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict
);
INSERT INTO tickets_comment VALUES(1,2,2,'Investigating the issue','2026-03-10T14:07:20.878841+00:00');
INSERT INTO tickets_comment VALUES(2,3,2,'Investigating the issue','2026-03-10T14:52:29.176047+00:00');
INSERT INTO tickets_comment VALUES(3,4,2,'Investigating the issue','2026-03-10T14:54:39.987280+00:00');
INSERT INTO tickets_comment VALUES(4,5,2,'Investigating the issue','2026-03-10T15:59:38.566972+00:00');
INSERT INTO tickets_comment VALUES(5,17,4,'Printer has been repaired successfully','2026-05-14T16:46:56.099595+00:00');
INSERT INTO tickets_comment VALUES(6,18,4,'Printer has been repaired successfully','2026-05-14T16:47:40.150406+00:00');
INSERT INTO tickets_comment VALUES(7,19,4,'Issue is no longer актуальна','2026-05-14T16:47:40.165570+00:00');
INSERT INTO tickets_comment VALUES(8,21,4,'Printer has been repaired successfully','2026-05-14T16:59:15.516159+00:00');
INSERT INTO tickets_comment VALUES(9,22,4,'Printer has been repaired successfully','2026-05-14T16:59:33.358952+00:00');
INSERT INTO tickets_comment VALUES(10,23,4,'Issue is no longer актуальна','2026-05-14T16:59:33.373397+00:00');
INSERT INTO tickets_comment VALUES(11,24,4,'Printer has been repaired successfully','2026-05-15T09:54:04.708948+00:00');
INSERT INTO tickets_comment VALUES(12,25,4,'Issue is no longer актуальна','2026-05-15T09:57:30.663780+00:00');
INSERT INTO tickets_comment VALUES(13,27,4,'Printer has been repaired successfully','2026-05-15T10:24:40.466596+00:00');
INSERT INTO tickets_comment VALUES(14,28,4,'Issue is no longer актуальна','2026-05-15T10:24:40.503660+00:00');
INSERT INTO tickets_comment VALUES(15,36,4,'Printer has been repaired successfully','2026-05-15T11:34:39.842145+00:00');
INSERT INTO tickets_comment VALUES(16,37,4,'Issue is no longer актуальна','2026-05-15T11:34:39.860417+00:00');
INSERT INTO tickets_comment VALUES(17,38,4,'Printer has been repaired successfully','2026-05-15T11:34:54.445050+00:00');
INSERT INTO tickets_comment VALUES(18,39,4,'Issue is no longer актуальна','2026-05-15T11:34:54.458887+00:00');
INSERT INTO tickets_comment VALUES(19,40,4,'Printer has been repaired successfully','2026-05-15T11:34:58.676821+00:00');
INSERT INTO tickets_comment VALUES(20,41,4,'Issue is no longer актуальна','2026-05-15T11:34:58.695587+00:00');
INSERT INTO tickets_comment VALUES(21,42,4,'Printer has been repaired successfully','2026-05-15T11:35:28.372041+00:00');
INSERT INTO tickets_comment VALUES(22,43,4,'Issue is no longer актуальна','2026-05-15T11:35:28.392428+00:00');
INSERT INTO tickets_comment VALUES(23,45,4,'Printer has been repaired successfully','2026-05-15T11:46:02.500098+00:00');
INSERT INTO tickets_comment VALUES(24,46,4,'Issue is no longer актуальна','2026-05-15T11:46:02.526703+00:00');
INSERT INTO tickets_comment VALUES(25,50,4,'Printer has been repaired successfully','2026-05-15T11:47:46.361320+00:00');
INSERT INTO tickets_comment VALUES(26,51,4,'Issue is no longer актуальна','2026-05-15T11:47:46.379108+00:00');
INSERT INTO tickets_comment VALUES(27,52,4,'Printer has been repaired successfully','2026-05-15T12:12:39.565248+00:00');
INSERT INTO tickets_comment VALUES(28,53,4,'Issue is no longer актуальна','2026-05-15T12:12:39.585504+00:00');
INSERT INTO tickets_comment VALUES(29,54,4,'Printer has been repaired successfully','2026-05-15T12:16:09.684638+00:00');
INSERT INTO tickets_comment VALUES(30,55,4,'Issue is no longer актуальна','2026-05-15T12:16:09.706123+00:00');
INSERT INTO tickets_comment VALUES(31,56,4,'Printer has been repaired successfully','2026-05-15T12:18:02.991862+00:00');
INSERT INTO tickets_comment VALUES(32,57,4,'Issue is no longer актуальна','2026-05-15T12:18:03.012968+00:00');
INSERT INTO tickets_comment VALUES(33,58,4,'Printer has been repaired successfully','2026-05-15T12:19:19.664566+00:00');
INSERT INTO tickets_comment VALUES(34,59,4,'Issue is no longer актуальна','2026-05-15T12:19:19.679598+00:00');
INSERT INTO tickets_comment VALUES(35,60,4,'Printer has been repaired successfully','2026-05-15T12:20:02.504247+00:00');
INSERT INTO tickets_comment VALUES(36,61,4,'Issue is no longer актуальна','2026-05-15T12:20:02.526559+00:00');
INSERT INTO tickets_comment VALUES(37,62,4,'Printer has been repaired successfully','2026-05-15T12:20:12.064241+00:00');
INSERT INTO tickets_comment VALUES(38,63,4,'Issue is no longer актуальна','2026-05-15T12:20:12.082673+00:00');
INSERT INTO tickets_comment VALUES(39,64,122,'string','2026-06-01T14:44:38.522968+00:00');
INSERT INTO tickets_comment VALUES(40,66,122,'frfgerfg','2026-06-04T11:23:29.080661+00:00');
INSERT INTO tickets_comment VALUES(41,66,122,'string','2026-06-04T11:25:07.616484+00:00');
INSERT INTO tickets_comment VALUES(42,67,122,'Коментарий','2026-06-04T12:26:18.602924+00:00');
INSERT INTO tickets_comment VALUES(43,67,122,'Долбаебы','2026-06-04T12:34:57.631702+00:00');
CREATE TABLE tickets_executor_assignment (
	executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	admin_id INTEGER, -- кто назначен
	ticket_id INTEGER,
	date_assignment TEXT,  
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete RESTRICT,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on DELETE restrict
);
INSERT INTO tickets_executor_assignment VALUES(1,2,2,'2026-03-10T14:07:20.878523+00:00');
INSERT INTO tickets_executor_assignment VALUES(2,2,3,'2026-03-10T14:52:29.175756+00:00');
INSERT INTO tickets_executor_assignment VALUES(3,2,4,'2026-03-10T14:54:39.987042+00:00');
INSERT INTO tickets_executor_assignment VALUES(4,2,5,'2026-03-10T15:59:38.566729+00:00');
INSERT INTO tickets_executor_assignment VALUES(5,4,36,'2026-05-15T11:34:39.832510+00:00');
INSERT INTO tickets_executor_assignment VALUES(6,4,38,'2026-05-15T11:34:54.437039+00:00');
INSERT INTO tickets_executor_assignment VALUES(7,4,40,'2026-05-15T11:34:58.666676+00:00');
INSERT INTO tickets_executor_assignment VALUES(8,4,42,'2026-05-15T11:35:28.363279+00:00');
INSERT INTO tickets_executor_assignment VALUES(9,4,44,'2026-05-15T11:36:09.454476+00:00');
INSERT INTO tickets_executor_assignment VALUES(10,4,45,'2026-05-15T11:46:02.485569+00:00');
INSERT INTO tickets_executor_assignment VALUES(11,14,50,'2026-05-15T11:47:46.353382+00:00');
INSERT INTO tickets_executor_assignment VALUES(12,14,52,'2026-05-15T12:12:39.558103+00:00');
INSERT INTO tickets_executor_assignment VALUES(13,14,54,'2026-05-15T12:16:09.674584+00:00');
INSERT INTO tickets_executor_assignment VALUES(14,4,56,'2026-05-15T12:18:02.968675+00:00');
INSERT INTO tickets_executor_assignment VALUES(15,14,56,'2026-05-15T12:18:02.980899+00:00');
INSERT INTO tickets_executor_assignment VALUES(16,4,58,'2026-05-15T12:19:19.649064+00:00');
INSERT INTO tickets_executor_assignment VALUES(17,14,58,'2026-05-15T12:19:19.657510+00:00');
INSERT INTO tickets_executor_assignment VALUES(18,14,60,'2026-05-15T12:20:02.482972+00:00');
INSERT INTO tickets_executor_assignment VALUES(19,14,60,'2026-05-15T12:20:02.493895+00:00');
INSERT INTO tickets_executor_assignment VALUES(20,14,62,'2026-05-15T12:20:12.043793+00:00');
INSERT INTO tickets_executor_assignment VALUES(21,14,62,'2026-05-15T12:20:12.054782+00:00');
INSERT INTO tickets_executor_assignment VALUES(22,24,64,'2026-06-01T14:43:48.609226+00:00');
CREATE TABLE tickets_status_record (
	ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	ticket_id INTEGER,
	admin_id INTEGER, -- кто установил статус
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on DELETE restrict
);
INSERT INTO tickets_status_record VALUES(1,2,1,'created','2026-03-10T14:07:20.876688+00:00');
INSERT INTO tickets_status_record VALUES(2,2,2,'at_work','2026-03-10T14:07:20.879072+00:00');
INSERT INTO tickets_status_record VALUES(3,2,2,'executed','2026-03-10T14:07:20.879245+00:00');
INSERT INTO tickets_status_record VALUES(4,3,1,'created','2026-03-10T14:52:29.171204+00:00');
INSERT INTO tickets_status_record VALUES(5,3,2,'at_work','2026-03-10T14:52:29.176268+00:00');
INSERT INTO tickets_status_record VALUES(6,3,2,'executed','2026-03-10T14:52:29.176420+00:00');
INSERT INTO tickets_status_record VALUES(7,4,1,'created','2026-03-10T14:54:39.986088+00:00');
INSERT INTO tickets_status_record VALUES(8,4,2,'at_work','2026-03-10T14:54:39.987494+00:00');
INSERT INTO tickets_status_record VALUES(9,4,2,'executed','2026-03-10T14:54:39.987651+00:00');
INSERT INTO tickets_status_record VALUES(10,5,1,'created','2026-03-10T15:59:38.565566+00:00');
INSERT INTO tickets_status_record VALUES(11,5,2,'at_work','2026-03-10T15:59:38.567180+00:00');
INSERT INTO tickets_status_record VALUES(12,5,2,'executed','2026-03-10T15:59:38.567643+00:00');
INSERT INTO tickets_status_record VALUES(13,6,4,'created','2026-05-14T16:31:14.273509+00:00');
INSERT INTO tickets_status_record VALUES(14,7,4,'created','2026-05-14T16:31:44.306332+00:00');
INSERT INTO tickets_status_record VALUES(15,8,4,'created','2026-05-14T16:32:27.899946+00:00');
INSERT INTO tickets_status_record VALUES(16,9,4,'created','2026-05-14T16:33:11.825406+00:00');
INSERT INTO tickets_status_record VALUES(17,10,4,'created','2026-05-14T16:34:32.494720+00:00');
INSERT INTO tickets_status_record VALUES(18,11,4,'created','2026-05-14T16:34:58.283435+00:00');
INSERT INTO tickets_status_record VALUES(19,12,4,'created','2026-05-14T16:35:17.816401+00:00');
INSERT INTO tickets_status_record VALUES(20,13,4,'created','2026-05-14T16:36:05.103295+00:00');
INSERT INTO tickets_status_record VALUES(21,14,4,'created','2026-05-14T16:36:28.064850+00:00');
INSERT INTO tickets_status_record VALUES(22,15,4,'created','2026-05-14T16:37:03.376871+00:00');
INSERT INTO tickets_status_record VALUES(23,16,4,'created','2026-05-14T16:44:04.363186+00:00');
INSERT INTO tickets_status_record VALUES(24,17,4,'created','2026-05-14T16:46:56.079400+00:00');
INSERT INTO tickets_status_record VALUES(25,17,4,'at_work','2026-05-14T16:46:56.090228+00:00');
INSERT INTO tickets_status_record VALUES(26,17,4,'executed','2026-05-14T16:46:56.099613+00:00');
INSERT INTO tickets_status_record VALUES(27,18,4,'created','2026-05-14T16:47:40.132278+00:00');
INSERT INTO tickets_status_record VALUES(28,18,4,'at_work','2026-05-14T16:47:40.141996+00:00');
INSERT INTO tickets_status_record VALUES(29,18,4,'executed','2026-05-14T16:47:40.150424+00:00');
INSERT INTO tickets_status_record VALUES(30,19,4,'created','2026-05-14T16:47:40.158662+00:00');
INSERT INTO tickets_status_record VALUES(31,19,4,'cancelled','2026-05-14T16:47:40.165587+00:00');
INSERT INTO tickets_status_record VALUES(32,20,4,'created','2026-05-14T16:58:58.745140+00:00');
INSERT INTO tickets_status_record VALUES(33,21,4,'created','2026-05-14T16:59:15.498518+00:00');
INSERT INTO tickets_status_record VALUES(34,21,4,'at_work','2026-05-14T16:59:15.507879+00:00');
INSERT INTO tickets_status_record VALUES(35,21,4,'executed','2026-05-14T16:59:15.516182+00:00');
INSERT INTO tickets_status_record VALUES(36,22,4,'created','2026-05-14T16:59:33.337036+00:00');
INSERT INTO tickets_status_record VALUES(37,22,4,'at_work','2026-05-14T16:59:33.350294+00:00');
INSERT INTO tickets_status_record VALUES(38,22,4,'executed','2026-05-14T16:59:33.358973+00:00');
INSERT INTO tickets_status_record VALUES(39,23,4,'created','2026-05-14T16:59:33.366886+00:00');
INSERT INTO tickets_status_record VALUES(40,23,4,'cancelled','2026-05-14T16:59:33.373415+00:00');
INSERT INTO tickets_status_record VALUES(41,24,4,'created','2026-05-15T09:51:53.208171+00:00');
INSERT INTO tickets_status_record VALUES(42,24,4,'at_work','2026-05-15T09:53:24.022717+00:00');
INSERT INTO tickets_status_record VALUES(43,24,4,'executed','2026-05-15T09:54:04.709005+00:00');
INSERT INTO tickets_status_record VALUES(44,25,4,'created','2026-05-15T09:57:24.979593+00:00');
INSERT INTO tickets_status_record VALUES(45,25,4,'cancelled','2026-05-15T09:57:30.663835+00:00');
INSERT INTO tickets_status_record VALUES(46,26,4,'created','2026-05-15T10:14:24.089285+00:00');
INSERT INTO tickets_status_record VALUES(47,26,4,'at_work','2026-05-15T10:22:48.891800+00:00');
INSERT INTO tickets_status_record VALUES(48,27,4,'created','2026-05-15T10:24:32.568490+00:00');
INSERT INTO tickets_status_record VALUES(49,27,4,'at_work','2026-05-15T10:24:34.135565+00:00');
INSERT INTO tickets_status_record VALUES(50,27,4,'executed','2026-05-15T10:24:40.466632+00:00');
INSERT INTO tickets_status_record VALUES(51,28,4,'created','2026-05-15T10:24:40.484516+00:00');
INSERT INTO tickets_status_record VALUES(52,28,4,'cancelled','2026-05-15T10:24:40.503693+00:00');
INSERT INTO tickets_status_record VALUES(53,29,4,'created','2026-05-15T10:25:06.470686+00:00');
INSERT INTO tickets_status_record VALUES(54,30,4,'created','2026-05-15T10:29:01.967992+00:00');
INSERT INTO tickets_status_record VALUES(55,31,4,'created','2026-05-15T10:31:31.026437+00:00');
INSERT INTO tickets_status_record VALUES(56,32,4,'created','2026-05-15T10:33:25.737578+00:00');
INSERT INTO tickets_status_record VALUES(57,32,4,'at_work','2026-05-15T10:33:48.623554+00:00');
INSERT INTO tickets_status_record VALUES(58,33,4,'created','2026-05-15T10:34:41.060815+00:00');
INSERT INTO tickets_status_record VALUES(59,34,4,'created','2026-05-15T11:16:26.619378+00:00');
INSERT INTO tickets_status_record VALUES(60,35,4,'created','2026-05-15T11:34:19.601157+00:00');
INSERT INTO tickets_status_record VALUES(61,36,4,'created','2026-05-15T11:34:39.821973+00:00');
INSERT INTO tickets_status_record VALUES(62,36,4,'at_work','2026-05-15T11:34:39.832502+00:00');
INSERT INTO tickets_status_record VALUES(63,36,4,'executed','2026-05-15T11:34:39.842163+00:00');
INSERT INTO tickets_status_record VALUES(64,37,4,'created','2026-05-15T11:34:39.851526+00:00');
INSERT INTO tickets_status_record VALUES(65,37,4,'cancelled','2026-05-15T11:34:39.860530+00:00');
INSERT INTO tickets_status_record VALUES(66,38,4,'created','2026-05-15T11:34:54.427975+00:00');
INSERT INTO tickets_status_record VALUES(67,38,4,'at_work','2026-05-15T11:34:54.437032+00:00');
INSERT INTO tickets_status_record VALUES(68,38,4,'executed','2026-05-15T11:34:54.445066+00:00');
INSERT INTO tickets_status_record VALUES(69,39,4,'created','2026-05-15T11:34:54.452145+00:00');
INSERT INTO tickets_status_record VALUES(70,39,4,'cancelled','2026-05-15T11:34:54.459001+00:00');
INSERT INTO tickets_status_record VALUES(71,40,4,'created','2026-05-15T11:34:58.654537+00:00');
INSERT INTO tickets_status_record VALUES(72,40,4,'at_work','2026-05-15T11:34:58.666669+00:00');
INSERT INTO tickets_status_record VALUES(73,40,4,'executed','2026-05-15T11:34:58.676837+00:00');
INSERT INTO tickets_status_record VALUES(74,41,4,'created','2026-05-15T11:34:58.686581+00:00');
INSERT INTO tickets_status_record VALUES(75,41,4,'cancelled','2026-05-15T11:34:58.695728+00:00');
INSERT INTO tickets_status_record VALUES(76,42,4,'created','2026-05-15T11:35:28.354335+00:00');
INSERT INTO tickets_status_record VALUES(77,42,4,'at_work','2026-05-15T11:35:28.363271+00:00');
INSERT INTO tickets_status_record VALUES(78,42,4,'executed','2026-05-15T11:35:28.372062+00:00');
INSERT INTO tickets_status_record VALUES(79,43,4,'created','2026-05-15T11:35:28.383176+00:00');
INSERT INTO tickets_status_record VALUES(80,43,4,'cancelled','2026-05-15T11:35:28.392584+00:00');
INSERT INTO tickets_status_record VALUES(81,44,4,'created','2026-05-15T11:36:05.011653+00:00');
INSERT INTO tickets_status_record VALUES(82,44,4,'at_work','2026-05-15T11:36:09.454462+00:00');
INSERT INTO tickets_status_record VALUES(83,45,4,'created','2026-05-15T11:46:02.473791+00:00');
INSERT INTO tickets_status_record VALUES(84,45,4,'at_work','2026-05-15T11:46:02.485562+00:00');
INSERT INTO tickets_status_record VALUES(85,45,4,'executed','2026-05-15T11:46:02.500116+00:00');
INSERT INTO tickets_status_record VALUES(86,46,4,'created','2026-05-15T11:46:02.511265+00:00');
INSERT INTO tickets_status_record VALUES(87,46,4,'cancelled','2026-05-15T11:46:02.526722+00:00');
INSERT INTO tickets_status_record VALUES(88,47,4,'created','2026-05-15T11:47:00.391974+00:00');
INSERT INTO tickets_status_record VALUES(89,48,4,'created','2026-05-15T11:47:27.328052+00:00');
INSERT INTO tickets_status_record VALUES(90,49,4,'created','2026-05-15T11:47:27.521898+00:00');
INSERT INTO tickets_status_record VALUES(91,50,4,'created','2026-05-15T11:47:46.345401+00:00');
INSERT INTO tickets_status_record VALUES(92,50,14,'at_work','2026-05-15T11:47:46.353374+00:00');
INSERT INTO tickets_status_record VALUES(93,50,4,'executed','2026-05-15T11:47:46.361337+00:00');
INSERT INTO tickets_status_record VALUES(94,51,4,'created','2026-05-15T11:47:46.370198+00:00');
INSERT INTO tickets_status_record VALUES(95,51,4,'cancelled','2026-05-15T11:47:46.379222+00:00');
INSERT INTO tickets_status_record VALUES(96,52,4,'created','2026-05-15T12:12:39.548413+00:00');
INSERT INTO tickets_status_record VALUES(97,52,14,'at_work','2026-05-15T12:12:39.558093+00:00');
INSERT INTO tickets_status_record VALUES(98,52,4,'executed','2026-05-15T12:12:39.565267+00:00');
INSERT INTO tickets_status_record VALUES(99,53,4,'created','2026-05-15T12:12:39.575501+00:00');
INSERT INTO tickets_status_record VALUES(100,53,4,'cancelled','2026-05-15T12:12:39.585618+00:00');
INSERT INTO tickets_status_record VALUES(101,54,4,'created','2026-05-15T12:16:09.664432+00:00');
INSERT INTO tickets_status_record VALUES(102,54,14,'at_work','2026-05-15T12:16:09.674578+00:00');
INSERT INTO tickets_status_record VALUES(103,54,4,'executed','2026-05-15T12:16:09.684655+00:00');
INSERT INTO tickets_status_record VALUES(104,55,4,'created','2026-05-15T12:16:09.695475+00:00');
INSERT INTO tickets_status_record VALUES(105,55,4,'cancelled','2026-05-15T12:16:09.706139+00:00');
INSERT INTO tickets_status_record VALUES(106,56,4,'created','2026-05-15T12:18:02.968654+00:00');
INSERT INTO tickets_status_record VALUES(107,56,14,'at_work','2026-05-15T12:18:02.980893+00:00');
INSERT INTO tickets_status_record VALUES(108,56,4,'executed','2026-05-15T12:18:02.991879+00:00');
INSERT INTO tickets_status_record VALUES(109,57,4,'created','2026-05-15T12:18:03.002700+00:00');
INSERT INTO tickets_status_record VALUES(110,57,4,'cancelled','2026-05-15T12:18:03.012985+00:00');
INSERT INTO tickets_status_record VALUES(111,58,4,'created','2026-05-15T12:19:19.649044+00:00');
INSERT INTO tickets_status_record VALUES(112,58,14,'at_work','2026-05-15T12:19:19.657504+00:00');
INSERT INTO tickets_status_record VALUES(113,58,4,'executed','2026-05-15T12:19:19.664583+00:00');
INSERT INTO tickets_status_record VALUES(114,59,4,'created','2026-05-15T12:19:19.672222+00:00');
INSERT INTO tickets_status_record VALUES(115,59,4,'cancelled','2026-05-15T12:19:19.679614+00:00');
INSERT INTO tickets_status_record VALUES(116,60,4,'created','2026-05-15T12:20:02.482948+00:00');
INSERT INTO tickets_status_record VALUES(117,60,14,'at_work','2026-05-15T12:20:02.493889+00:00');
INSERT INTO tickets_status_record VALUES(118,60,4,'executed','2026-05-15T12:20:02.504263+00:00');
INSERT INTO tickets_status_record VALUES(119,61,4,'created','2026-05-15T12:20:02.515319+00:00');
INSERT INTO tickets_status_record VALUES(120,61,4,'cancelled','2026-05-15T12:20:02.526574+00:00');
INSERT INTO tickets_status_record VALUES(121,62,4,'created','2026-05-15T12:20:12.043773+00:00');
INSERT INTO tickets_status_record VALUES(122,62,14,'at_work','2026-05-15T12:20:12.054777+00:00');
INSERT INTO tickets_status_record VALUES(123,62,4,'executed','2026-05-15T12:20:12.064258+00:00');
INSERT INTO tickets_status_record VALUES(124,63,4,'created','2026-05-15T12:20:12.073792+00:00');
INSERT INTO tickets_status_record VALUES(125,63,4,'cancelled','2026-05-15T12:20:12.082688+00:00');
INSERT INTO tickets_status_record VALUES(126,64,122,'created','2026-06-01T14:34:56.078556+00:00');
INSERT INTO tickets_status_record VALUES(127,64,24,'at_work','2026-06-01T14:43:48.609217+00:00');
INSERT INTO tickets_status_record VALUES(128,64,122,'executed','2026-06-01T14:44:38.522986+00:00');
INSERT INTO tickets_status_record VALUES(129,65,122,'created','2026-06-04T11:23:11.891604+00:00');
INSERT INTO tickets_status_record VALUES(130,66,122,'created','2026-06-04T11:23:29.080643+00:00');
INSERT INTO tickets_status_record VALUES(131,66,122,'deferred','2026-06-04T11:23:52.864372+00:00');
INSERT INTO tickets_status_record VALUES(132,66,122,'cancelled','2026-06-04T11:25:07.616502+00:00');
INSERT INTO tickets_status_record VALUES(133,67,122,'created','2026-06-04T12:26:18.602906+00:00');
INSERT INTO tickets_status_record VALUES(134,67,122,'cancelled','2026-06-04T12:34:57.631722+00:00');
INSERT INTO tickets_status_record VALUES(135,68,160,'created','2026-06-08T14:43:29.102654+00:00');
CREATE TABLE user_tickets_comment (
	user_comment_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	employee_id INTEGER,
	comment TEXT,
	date_created TEXT,
	CONSTRAINT comment_tickets_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT comment_tickets_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
INSERT INTO user_tickets_comment VALUES(1,1,10,'Please fix ASAP','2026-03-16T11:29:27.227543+00:00');
INSERT INTO user_tickets_comment VALUES(2,2,10,'Please fix ASAP','2026-03-16T11:29:39.228139+00:00');
CREATE TABLE user_tickets_status_record (
	user_ticket_status_record_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	employee_id INTEGER,
	user_ticket_id INTEGER,
	status TEXT,
	date_created TEXT,
	CONSTRAINT tickets_status_record_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
	CONSTRAINT tickets_status_record_employees_FK FOREIGN KEY (employee_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO user_tickets_status_record VALUES(1,10,1,'created','2026-03-16T11:29:27.225254+00:00');
INSERT INTO user_tickets_status_record VALUES(2,10,1,'created','2026-03-16T11:29:27.225262+00:00');
INSERT INTO user_tickets_status_record VALUES(3,10,1,'confirmed','2026-03-16T11:29:27.226731+00:00');
INSERT INTO user_tickets_status_record VALUES(4,1,1,'at_work','2026-03-16T11:29:27.227832+00:00');
INSERT INTO user_tickets_status_record VALUES(5,1,1,'executed','2026-03-16T11:29:27.227974+00:00');
INSERT INTO user_tickets_status_record VALUES(6,10,2,'created','2026-03-16T11:29:39.226973+00:00');
INSERT INTO user_tickets_status_record VALUES(7,10,2,'created','2026-03-16T11:29:39.226981+00:00');
INSERT INTO user_tickets_status_record VALUES(8,10,2,'confirmed','2026-03-16T11:29:39.227934+00:00');
INSERT INTO user_tickets_status_record VALUES(9,1,2,'at_work','2026-03-16T11:29:39.228344+00:00');
INSERT INTO user_tickets_status_record VALUES(10,1,2,'executed','2026-03-16T11:29:39.228457+00:00');
INSERT INTO user_tickets_status_record VALUES(11,67,3,'created','2026-05-15T12:50:22.700974+00:00');
INSERT INTO user_tickets_status_record VALUES(12,67,4,'created','2026-05-15T12:50:41.392675+00:00');
INSERT INTO user_tickets_status_record VALUES(13,67,5,'created','2026-05-15T12:53:13.470686+00:00');
INSERT INTO user_tickets_status_record VALUES(14,67,6,'created','2026-05-15T12:58:13.522010+00:00');
INSERT INTO user_tickets_status_record VALUES(15,67,7,'created','2026-05-15T13:00:16.095883+00:00');
INSERT INTO user_tickets_status_record VALUES(16,67,7,'canceled_by_client','2026-05-15T13:00:16.107644+00:00');
CREATE TABLE user_tickets_executor_assignments (
	user_executor_assignment_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_ticket_id INTEGER,
	admin_id INTEGER,
	date_assignment TEXT,
	CONSTRAINT executor_assignments_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT executor_assignments_tickets_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict
);
CREATE TABLE tickets (
	ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- клиент
	admin_id INTEGER, -- создатель заявки
	user_id INTEGER DEFAULT NULL, -- заявитель от клиента, может не быть
	user_ticket_contact_user_id INTEGER NULL, -- контактное лицо от клиента. может не быть
	user_ticket_id INTEGER DEFAULT NULL, -- связь с заявкой созданной пользователем клиентом, может не быть 
	text_of_ticket TEXT, -- текст заявки
	date_created TEXT, -- дата создания
	is_remote INTEGER DEFAULT (0), -- сделана удаленно, возможно удаленное решение
	is_closed INTEGER DEFAULT (0), -- заявка завершена
	date_closed TEXT, -- дата завершения или снятия заявки
	urgency_level INTEGER DEFAULT (0), -- срочная или несрочная 
        department_id INTEGER DEFAULT NULL,
	version INTEGER, description TEXT, -- версия
	CONSTRAINT tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT tickets_admin_FK FOREIGN KEY (admin_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT tickets_user_user_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT tickets_user_ticket_FK FOREIGN KEY (user_ticket_id) REFERENCES user_tickets(user_ticket_id) on delete restrict,
        CONSTRAINT tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES employees(employee_id) on delete restrict,
        CONSTRAINT tickets_departments_FK FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
CREATE TABLE user_tickets (
	user_ticket_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	client_id INTEGER, -- заявки от какого клиента
	user_id INTEGER, -- кто создал заявку
	user_ticket_contact_user_id INTEGER DEFAULT NULL, -- контактное лицо по заявке, может не быть
	text_of_ticket TEXT, -- текст заявки 
	date_created TEXT,
	version INTEGER, 
	date_closed TEXT, -- дата завершения или снятия заявки 
	is_closed INTEGER,
	CONSTRAINT user_tickets_users_FK FOREIGN KEY (user_id) REFERENCES employees(employee_id) on delete restrict,
	CONSTRAINT user_tickets_clients_FK FOREIGN KEY (client_id) REFERENCES clients(client_id) on delete restrict,
	CONSTRAINT user_tickets_user_ticket_contact_user_FK FOREIGN KEY (user_ticket_contact_user_id) REFERENCES employees(employee_id) on delete restrict
);
INSERT INTO user_tickets VALUES(1,1,10,NULL,'Printer does not work','2026-03-16T11:29:27.225216+00:00',0,NULL,0);
INSERT INTO user_tickets VALUES(2,1,10,NULL,'Printer does not work','2026-03-16T11:29:39.226955+00:00',0,NULL,0);
INSERT INTO user_tickets VALUES(3,4,67,67,'Printer problem 20260515155022','2026-05-15T12:50:22.700987+00:00',0,NULL,0);
INSERT INTO user_tickets VALUES(4,4,67,67,'Printer problem 20260515155041','2026-05-15T12:50:41.392686+00:00',1,NULL,0);
INSERT INTO user_tickets VALUES(5,4,67,67,'Printer problem 20260515155311','2026-05-15T12:53:13.470707+00:00',0,NULL,0);
INSERT INTO user_tickets VALUES(6,4,67,67,'Printer problem 20260515155810','2026-05-15T12:58:13.522030+00:00',0,NULL,0);
INSERT INTO user_tickets VALUES(7,4,67,67,'Printer problem 20260515160016','2026-05-15T13:00:16.095893+00:00',1,'2026-05-15T13:00:16.107648+00:00',1);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('employees',172);
INSERT INTO sqlite_sequence VALUES('accounts',493);
INSERT INTO sqlite_sequence VALUES('roles',66);
INSERT INTO sqlite_sequence VALUES('clients',25);
INSERT INTO sqlite_sequence VALUES('tickets',68);
INSERT INTO sqlite_sequence VALUES('tickets_status_record',135);
INSERT INTO sqlite_sequence VALUES('tickets_executor_assignment',22);
INSERT INTO sqlite_sequence VALUES('tickets_comment',43);
INSERT INTO sqlite_sequence VALUES('user_tickets',7);
INSERT INTO sqlite_sequence VALUES('user_tickets_status_record',16);
INSERT INTO sqlite_sequence VALUES('user_tickets_comment',2);
INSERT INTO sqlite_sequence VALUES('departments',1);
CREATE UNIQUE INDEX accounts_login_IDX ON accounts (login);
CREATE UNIQUE INDEX accounts_employee_uq ON accounts(employee_id);
CREATE UNIQUE INDEX idx_departments_name
ON departments(name);
COMMIT;

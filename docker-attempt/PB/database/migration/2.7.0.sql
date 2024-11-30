-- Update the Database schema from 2.6.0 to 2.7.0
-- New flexible role based access system for website

-- List of roles
CREATE TABLE roles (
	id INT UNSIGNED AUTO_INCREMENT NOT NULL,
	name TEXT NOT NULL,
	is_system_role INT(1) UNSIGNED NOT NULL DEFAULT 0,
	description TEXT,
	PRIMARY KEY (id)
);

-- Create the default roles
INSERT INTO roles(name, is_system_role, description) VALUES
	('unauthenticated', 1, 'Role of users who have not authenticated'),
	('user', 1, 'Role of authenticated users who have not be granted additional permissions. This role is the default for users created in the web interface.'),
	('admin', 1, 'Role for users who administer the system.'),
	('trainer', 0, 'Role for trainers created for backward compatibility with student designed system');


-- List of Permissions
-- Permissions play a special role in the code and are therefore constants in
-- in code and not AUTO_INCREMENT. See Entity/Permissions.php in Management
-- Portal. A backing table is provided to enforce a constraint in
-- roles_x_permissions
CREATE TABLE permissions (
	id INT UNSIGNED NOT NULL,
	name TEXT NOT NULL,
	PRIMARY KEY (id)
);

INSERT INTO permissions(id, name) VALUES
	(1, 'CREATE_API_KEY'),
	(2, 'READ_API_KEY'),
	(3, 'MODIFY_API_KEY'),
	(4, 'DELETE_API_KEY'),
	(5, 'LIST_API_KEYS'),
	(101, 'CREATE_EQUIPMENT_AUTHORIZATION'),
	(104, 'DELETE_EQUIPMENT_AUTHORIZATION'),
	(105, 'LIST_EQUIPMENT_AUTHORIZATIONS'),
	(106, 'LIST_OWN_EQUIPMENT_AUTHORIZATIONS'),
	(205, 'LIST_CARD_TYPES'),
	(301, 'CREATE_CARD'),
	(302, 'READ_CARD'),
	(303, 'MODIFY_CARD'),
	(305, 'LIST_CARDS'),
	(306, 'LIST_OWN_CARDS'),
	(401, 'CREATE_CHARGE_POLICY'),
	(402, 'READ_CHARGE_POLICY'),
	(403, 'MODIFY_CHARGE_POLICY'),
	(404, 'DELETE_CHARGE_POLICY'),
	(405, 'LIST_CHARGE_POLICIES'),
	(501, 'CREATE_CHARGE'),
	(502, 'READ_CHARGE'),
	(503, 'MODIFY_CHARGE'),
	(504, 'DELETE_CHARGE'),
	(505, 'LIST_CHARGES'),
	(506, 'LIST_OWN_CHANGES'),
	(601, 'CREATE_EQUIPMENT_TYPE'),
	(602, 'READ_EQUIPMENT_TYPE'),
	(603, 'MODIFY_EQUIPMENT_TYPE'),
	(604, 'DELETE_EQUIPMENT_TYPE'),
	(605, 'LIST_EQUIPMENT_TYPES'),
	(701, 'CREATE_EQUIPMENT'),
	(702, 'READ_EQUIPMENT'),
	(703, 'MODIFY_EQUIPMENT'),
	(704, 'DELETE_EQUIPMENT'),
	(705, 'LIST_EQUIPMENT'),
	(801, 'CREATE_LOCATION'),
	(802, 'READ_LOCATION'),
	(803, 'MODIFY_LOCATION'),
	(804, 'DELETE_LOCATION'),
	(805, 'LIST_LOCATIONS'),
	(902, 'READ_LOG'),
	(905, 'LIST_LOGS'),
	(1001, 'CREATE_PAYMENT'),
	(1002, 'READ_PAYMENT'),
	(1003, 'MODIFY_PAYMENT'),
	(1004, 'DELETE_PAYMENT'),
	(1005, 'LIST_PAYMENTS'),
	(1006, 'LIST_OWN_PAYMENTS'),
	(1101, 'CREATE_ROLE'),
	(1102, 'READ_ROLE'),
	(1103, 'MODIFY_ROLE'),
	(1104, 'DELETE_ROLE'),
	(1105, 'LIST_ROLES'),
	(1201, 'CREATE_USER'),
	(1202, 'READ_USER'),
	(1203, 'MODIFY_USER'),
	(1204, 'DELETE_USER'),
	(1205, 'LIST_USERS'),
	(1206, 'READ_OWN_USER');


-- Associate Permissions with roles.
CREATE TABLE roles_x_permissions (
	id INT UNSIGNED AUTO_INCREMENT NOT NULL,
	role_id INT UNSIGNED NOT NULL,
	permission_id INT UNSIGNED NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY roles_x_permissions_role_id (role_id) REFERENCES roles (id) ON DELETE CASCADE,
	FOREIGN KEY roles_x_permissions_permission_id (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

-- Assign default permissions to roles
-- Assign permissions for an unauthenticated user
SET @unauthenticated_role_id = (SELECT id FROM roles WHERE name = 'unauthenticated');
INSERT INTO roles_x_permissions(role_id, permission_id) VALUES
	(@unauthenticated_role_id, 605),	-- list equipment types
	(@unauthenticated_role_id, 705);	-- list equipment

-- Assign permissions for a default authenticated user
SET @user_role_id = (SELECT id FROM roles WHERE name = 'user');
INSERT INTO roles_x_permissions(role_id, permission_id) VALUES
	(@user_role_id, 106),	-- list own authorizations
	(@user_role_id, 306),	-- list own cards
	(@user_role_id, 506),	-- read own charges
	(@user_role_id, 605),	-- list equipment types
	(@user_role_id, 705),	-- list equipment
	(@user_role_id, 1006),	-- read own payments
	(@user_role_id, 1206);	-- read own user record

-- Assign permissions for administrators ie. all permissions
SET @admin_role_id = (SELECT id FROM roles WHERE name = 'admin');
INSERT INTO roles_x_permissions(role_id, permission_id) VALUES
	(@admin_role_id, 1),
	(@admin_role_id, 2),
	(@admin_role_id, 3),
	(@admin_role_id, 4),
	(@admin_role_id, 5),
	(@admin_role_id, 101),
	(@admin_role_id, 104),
	(@admin_role_id, 105),
	(@admin_role_id, 106),
	(@admin_role_id, 205),
	(@admin_role_id, 301),
	(@admin_role_id, 302),
	(@admin_role_id, 303),
	(@admin_role_id, 305),
	(@admin_role_id, 306),
	(@admin_role_id, 405),
	(@admin_role_id, 501),
	(@admin_role_id, 502),
	(@admin_role_id, 503),
	(@admin_role_id, 504),
	(@admin_role_id, 505),
	(@admin_role_id, 506),
	(@admin_role_id, 601),
	(@admin_role_id, 602),
	(@admin_role_id, 603),
	(@admin_role_id, 604),
	(@admin_role_id, 605),
	(@admin_role_id, 701),
	(@admin_role_id, 702),
	(@admin_role_id, 703),
	(@admin_role_id, 704),
	(@admin_role_id, 705),
	(@admin_role_id, 801),
	(@admin_role_id, 802),
	(@admin_role_id, 803),
	(@admin_role_id, 804),
	(@admin_role_id, 805),
	(@admin_role_id, 902),
	(@admin_role_id, 905),
	(@admin_role_id, 1001),
	(@admin_role_id, 1002),
	(@admin_role_id, 1003),
	(@admin_role_id, 1004),
	(@admin_role_id, 1005),
	(@admin_role_id, 1006),
	(@admin_role_id, 1101),
	(@admin_role_id, 1102),
	(@admin_role_id, 1103),
	(@admin_role_id, 1104),
	(@admin_role_id, 1105),
	(@admin_role_id, 1201),
	(@admin_role_id, 1202),
	(@admin_role_id, 1203),
	(@admin_role_id, 1204),
	(@admin_role_id, 1205),
	(@admin_role_id, 1206);

-- Trainer was part of the 1.x design but a full fledged RBA means ends users
-- can design their own roles. Future revisions will not reference this role.
SET @trainer_role_id = (SELECT id FROM roles WHERE name = 'trainer');
INSERT INTO roles_x_permissions(role_id, permission_id) VALUES
	(@trainer_role_id, 101),	-- create authorizations
	(@trainer_role_id, 104),	-- delete authorizations
	(@trainer_role_id, 105),	-- list authorizations
	(@trainer_role_id, 106),	-- list own authorizations
	(@trainer_role_id, 306),	-- list own cards
	(@trainer_role_id, 506),	-- read own charges
	(@trainer_role_id, 602),	-- read eqipment type
	(@trainer_role_id, 605),	-- list equipment types
	(@trainer_role_id, 702),	-- read equipment
	(@trainer_role_id, 705),	-- list equipment
	(@trainer_role_id, 1202),	-- read user
	(@trainer_role_id, 1205),	-- list users
	(@trainer_role_id, 1206);	-- read own user record


-- ALTER USER add role_id, foreign key to roles
ALTER TABLE users ADD role_id INT UNSIGNED NOT NULL DEFAULT 0;
ALTER TABLE users ADD CONSTRAINT users_role_id FOREIGN KEY (role_id) REFERENCES roles(id);


-- Update users setting role_id appropriate to management portal access level
UPDATE users SET role_id = @user_role_id WHERE management_portal_access_level_id = 1;
UPDATE users SET role_id = @trainer_role_id WHERE management_portal_access_level_id = 2;
UPDATE users SET role_id = @admin_role_id WHERE management_portal_access_level_id = 3;


-- DROP the management_portal Access Foreign Key
ALTER TABLE users DROP FOREIGN KEY users_management_portal_access_level_id;
ALTER TABLE users DROP COLUMN management_portal_access_level_id;


-- we no longer use the management portal access level design
-- therefore we don't require the backing table
DROP TABLE management_portal_access_levels;

-- we need to add the delete cascade for authorizations in order for testing to work
ALTER TABLE authorizations
	DROP FOREIGN KEY authorizations_user_id,
	DROP FOREIGN KEY authorizations_equipment_type_id;
ALTER TABLE authorizations
	ADD CONSTRAINT authorizations_equipment_type_id FOREIGN KEY (equipment_type_id) REFERENCES equipment_types (id) ON DELETE CASCADE,
	ADD CONSTRAINT authorizations_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;


INSERT INTO schema_versioning(version, comment) VALUES ("2.7.0", "Migration Complete");

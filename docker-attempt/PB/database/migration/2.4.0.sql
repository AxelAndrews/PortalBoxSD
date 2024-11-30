-- Update the Database schema from 2.3.0 to 2.4.0

ALTER TABLE users ADD is_active INT(1) UNSIGNED;
UPDATE users SET is_active = 1;
ALTER TABLE users MODIFY is_active INT(1) UNSIGNED NOT NULL;

INSERT INTO schema_versioning(version, comment) VALUES ("2.4.0", "Migration Complete");
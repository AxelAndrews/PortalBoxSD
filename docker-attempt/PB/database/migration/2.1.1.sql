-- Update the Database schema from 2.1.0 to 2.1.1

ALTER TABLE users MODIFY email VARCHAR(512) NOT NULL;
ALTER TABLE users ADD CONSTRAINT users_email UNIQUE (email);

INSERT INTO schema_versioning(version, comment) VALUES ("2.1.1", "Migration Complete");
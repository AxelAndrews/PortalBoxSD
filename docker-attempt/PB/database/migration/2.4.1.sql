-- Update the Database schema from 2.4.0 to 2.4.1

ALTER TABLE users ADD comment TEXT;

INSERT INTO schema_versioning(version, comment) VALUES ("2.4.1", "Migration Complete");
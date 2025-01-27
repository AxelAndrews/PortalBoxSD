-- Update the Database schema from 2.1.0 to 2.1.1

INSERT INTO event_types(name) VALUES
	("Startup Complete"),
	("Planned Shutdown");
ALTER TABLE log MODIFY card_id BIGINT(20) UNSIGNED;

INSERT INTO schema_versioning(version, comment) VALUES ("2.2.0", "Migration Complete");
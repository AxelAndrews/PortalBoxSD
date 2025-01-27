-- Update the Database schema from 2.2.0 to 2.3.0

ALTER TABLE equipment ADD in_service INT(1) UNSIGNED;
UPDATE equipment SET in_service = 1;
ALTER TABLE equipment MODIFY in_service INT(1) UNSIGNED NOT NULL;

INSERT INTO schema_versioning(version, comment) VALUES ("2.3.0", "Migration Complete");
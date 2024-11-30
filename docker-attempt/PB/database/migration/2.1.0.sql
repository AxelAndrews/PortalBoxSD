-- Update the Database schema from 2.0.0 to 2.1.0

CREATE TABLE api_keys (
	id INT UNSIGNED AUTO_INCREMENT NOT NULL,
	name TEXT NOT NULL,
	token CHAR(32) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE schema_versioning (
	id INT UNSIGNED AUTO_INCREMENT NOT NULL,
	time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	version TEXT NOT NULL,
	comment TEXT,
	PRIMARY KEY(id)
);

INSERT INTO schema_versioning(version, comment) VALUES ("2.1.0", "Migration Complete");
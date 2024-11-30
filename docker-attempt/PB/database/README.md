# Portal Box Database

## About
The Portal Box system is composed of one or more IoT access control boxes and a management website all of which communicate through the database. This project defines the schema for that database.

### Note on Conventions
In some shell commands you may need to provide values left up to you. These values are denoted using the semi-standard shell variable syntax e.g. ${NAME_OF_DATA} 

## License
This project is licensed under the Apache 2.0 License - see the LICENSE file for details

## Dependancies
A MySQL or compatible (MariaDB) database
A database user with CALL, CREATE, DROP, INSERT, SELECT priveleges

## Database Priveledge Recommendations
Some hosting setups will only provide a single database user account with all permissions on a single schema. This is sufficient. You can however possibly increase security by creating a second user used by the Portal Boxes to connect to the Database with only SELECT, INSERT and CALL priveleges. The web interface requires SELECT, INSERT, and UPDATE priveleges.

## Installing
The `schema` directory contains a script which drops the data form a specified database and creates the table stucture (schema) of the current up to date database. The `migration` directory contains scripts that will modify an existing Portal Box database updating the schema from one version to the next.

[WARNING] Using the script in `schema` will cause the loss of data if used on an existing Portal Box database by design. It is to be used with new databases and as a last resort recovery option only.

To set up a new database, clone this repository somewhere accessible from the command line, with the mysql cli available and able to connect to the database; then issue:

```sh
cd ${PATH_TO_PROJECT}
mysql -h ${YOUR_MYSQL_SERVER_HOSTNAME} -u ${YOUR_MYSQL_USERNAME} -p ${YOUR_MYSQL_DATABSE_NAME} < schema/schema.sql
```

Enter your database password when prompted and your database should be created in a few moments. You will need to add at least an administrative user to get started with the Management Portal.

```mysql
INSERT INTO users(name, email, management_portal_access_level_id) VALUES(${YOUR_NAME}, ${YOUR_EMAIL_ADDRESS}, 3);
```

To update from one schema to the next eg 2.0.0 the initial release to 2.1.0 the first update do:

```sh
mysql -h ${YOUR_MYSQL_SERVER_HOSTNAME} -u ${YOUR_MYSQL_USERNAME} -p ${YOUR_MYSQL_DATABSE_NAME} < migration/2.1.0.sql
```

at the command line and enter your database user's password when prompted.

## Roadmap
- Create script to create an administrative user

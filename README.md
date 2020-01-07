This is the back-end of the Fronter software


## Reset PostgreSQL Database

1. Login to Rancher and access PostgreSQL Shell
2. Execute `psql -U postgres`
3. Prompt will expect password which can be found in Rancher Secrets
4. Execute `\c elitedocdb` which will connect you to the database (change database name if necessary)
5. Execute `DROP SCHEMA public CASCADE;` to drop all the tables and types
6. Execute `CREATE SCHEMA public;` to recreate the schema

This is the back-end of the Fronter software

## Running Locally in Docker:

1. Create a _data/ sub-directory within the ./docker/ directory so we can map to it a volume for the PostgreSQL service.

2. Build the docker images:
   ```
   $ docker-compose build
   ```
3. Run the images:
   ```
   $ docker-compose up
   ```
4. **In a new terminal window/tab**, start an interactive shell session in the `api` container:
   ```
   $ docker exec -it api sh
   ```
5. Create the DB file and tables:
   ```
   /app # python manage.py db upgrade
   ```
6. Plant the seed data in the DB tables:
   ```
   /app # python manage.py seed
   ```
7. Exit the interactive shell session:
   ```
   /app # exit
   ```
8. That's it! You can now login via the frontend with the following credentials:
   ```
   username: admin
   password: password
   ```

## Setting Up Environment Variables in Docker

The app depends on certain environment variables to be available to it. You can define these variables by filling in the following file and saving it as `./docker/api.env`:

```
DB_CONN_STRING=
SCRAPY_SETTINGS_MODULE=
SCRAPYJS_URL=
SECRET_KEY=
SMART_CREDIT_CLIENT_KEY=
SMART_CREDIT_PUBLISHER_ID=
SMART_CREDIT_SPONSOR_CODE=
DATAX_URL=
DATAX_LICENSE_KEY=
DATAX_PASSWORD=
DATAX_CALL_TYPE=
AWS_ACCOUNT_ID=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

## Swagger Docs Endpoint

`http://localhost:5000/api/v1/`

## Connect Your Favorite Client to development PostgreSQL Service

Postgresql service maps port 5432 to your host computer so you can connect your favorite PostgreSQL GUI client to it on localhost:5432. 
For user, password and DB name, review docker-compose.yml file where these are defined under "dbsvc" service.

## Reset PostgreSQL Database

1. Login to Rancher and access PostgreSQL Shell
2. Execute `psql -U postgres`
3. Prompt will expect password which can be found in Rancher Secrets
4. Execute `\c elitedocdb` which will connect you to the database (change database name if necessary)
5. Execute `DROP SCHEMA public CASCADE;` to drop all the tables and types
6. Execute `CREATE SCHEMA public;` to recreate the schema

## DB Migrations

Flask-Migrate (a wrapper for Alembic) is leveraged in this project for any work that impacts DB schema. All contributing developers must 
ensure that their pull requests are atomic; these must contain everything to successfully run by other developers. And these include 
DB migrations, if applicable. Always communicate an intended PR with the team when your work includes a migration. Sequencing of migrations 
should be coordinated with the team and a rebase may be required on your part.

# Migration Creation

When you run the command to migrate, Flask-Migrate will carry out a comparison of current models + DB state and generate a migration 
file representing deltas. Here's how to create a new migration for your work.

1. First, check your current ("head") migration version within the api container.
   ```
   $ docker exec -it api sh
   $ pyton manage.py db current
   ```
2. Generate a migration and check that the corresponding migration file was introduced (but not yet applied).
   ```
   $ python manage.py db migrate -m "Added Notes feature"
   $ python manage.py db history
   $ python manage.py db current
   ```

# Migrations Upgrade & Downgrade

Simply generating a migration does not automatically apply it. You will need to run it (upgrade). Removing it involves a downgrade. 

1. Upgrade your schema by running any new migrations
   ```
   $ python manage.py db upgrade
   $ python manage.py db current
   ```
2. And you should always ensure the downgrade (rolling back to previous version) also works at the time of your migration creation.
   ```
   $ python manage.py db downgrade
   $ python manage.py db current
   ```

# Resolving Migration Conflicts

Migration conflicts will may eventually occur and knowing how to resolve is important. Please read up on this topic in the following aricle.
https://blog.miguelgrinberg.com/post/resolving-database-schema-conflicts
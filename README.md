This is the back-end of the Fronter software

## Running Locally in Docker:

1. Build the docker images:
   ```
   $ docker-compose build
   ```
2. Run the images:
   ```
   $ docker-compose up
   ```
3. **In a new terminal window/tab**, start an interactive shell session in the `api` container:
   ```
   $ docker exec -it api sh
   ```
4. Create the DB file and tables:
   ```
   /app # python manage.py db upgrade
   ```
5. Plant the seed data in the DB tables:
   ```
   /app # python manage.py seed
   ```
6. Exit the interactive shell session:
   ```
   /app # exit
   ```
7. That's it! You can now login via the frontend with the following credentials:
   ```
   username: admin
   password: password
   ```

## Setting Up Environment Variables in Docker

The app depends on certain environment variables to be available to it. You can define these variables by filling in the following file and saving it as `./docker/api.env`:

```
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

## Reset PostgreSQL Database

1. Login to Rancher and access PostgreSQL Shell
2. Execute `psql -U postgres`
3. Prompt will expect password which can be found in Rancher Secrets
4. Execute `\c elitedocdb` which will connect you to the database (change database name if necessary)
5. Execute `DROP SCHEMA public CASCADE;` to drop all the tables and types
6. Execute `CREATE SCHEMA public;` to recreate the schema

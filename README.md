# create-flask-app
Simple flask app to start a B2B SaaS product with batteries included and exposed SQL.

## Installation
Get the project files to the current directory with the following command:
```wget https://github.com/sylvain-josserand/create-flask-app/archive/refs/heads/main.zip && unzip main.zip && mv -n create-flask-app-main/{.,}* ./ && rmdir create-flask-app-main && rm main.zip```

This will download the project files and unzip them in the current directory.

Use them as a starting point for your own project.

## Usage

### 1. Create the database

Use the `migrate.py` script to apply all migrations to the main database and all the accounts databases.

```python migrate.py```

### 2. Customize the config.ini

Edit the config.ini file and fill the values with yours

### 3. Launch the app server

Run the app in development mode with the following command:

```FLASK_ENV=development FLASK_DEBUG=true flask run```

### 4. Test the app

Run the tests with the following command:

```python test.py```

## Completed features
 - Guest access without signup
 - Separation of account into separate database files
 - Databases migration
 - Save guest work upon signup
 - Authentication by email and password
 - User account management: change name and email, change password, delete
 - Company "multi-user" account management: create, rename and delete account, change role
 - Invite users to company account
 - 80% test coverage
 - Reset forgotten password by email
 - Use Bootstrap 5 for the UI

## To-do list
 - Email verification
 - OAuth2 authentication (Google, Facebook, etc.)
 - Automated server deployment with production-ready settings

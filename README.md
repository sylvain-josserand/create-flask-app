# create-flask-app
Simple flask app to start a B2B SaaS product

## Installation
Get the project files with the following command:
```wget https://github.com/sylvain-josserand/create-flask-app/archive/refs/heads/main.zip && unzip -j main.zip create-flask-app-main/*```

This will download the project files and unzip them in the current directory.

Use them as a starting point for your own project.

## Usage

### Database migration

Use the `migrate.py` script to apply all migrations to the main database and all the accounts databases.

```python migrate.py```

### Run the app

Run the app in development mode with the following command:

```FLASK_ENV=development FLASK_DEBUG=true flask run```

### Test the app

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

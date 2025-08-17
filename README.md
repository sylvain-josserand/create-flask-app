# create-flask-app
Simple flask app to start a B2B SaaS product with batteries included and exposed SQL.

## Installation
Get the project files to the current directory with the following command:
```curl -L https://github.com/sylvain-josserand/create-flask-app/archive/refs/heads/main.tar.gz | tar -xz --strip-components=1```

This will download the project files and unzip them in the current directory.

Use them as a starting point for your own project.

## Usage

### 1. Install your python environment

Make sure Python 3.13 (`python -V`) is installed.
Create a virtual environment in the `.venv` directory at the root of the project: `python -m venv ./.venv`
Activate the environment so that pip will install the packages in the env instead of system-wide: `. ./.venv/bin/activate`
Install the project's required packages: `pip install -r ./requirements.txt`

### 2. Create the database

Use the `migrate.py` script to apply all migrations to the main database and all the accounts databases.

```python migrate.py```

### 3. Customize the config.ini

Edit the config.ini file and fill the values with yours

### 4. Launch the app server

Run the app in development mode with the following command:

```FLASK_ENV=development FLASK_DEBUG=true flask run```

### 5. Test the app

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
 - Use custom CSS for the UI

## To-do list
 - Email verification
 - OAuth2 authentication (Google, Facebook, etc.)
 - Automated server deployment with production-ready settings

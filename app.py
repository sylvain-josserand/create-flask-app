import secrets
from configparser import ConfigParser
from datetime import timedelta
from pathlib import Path

from flask import Flask


def create_app(config_update=None):
    app = Flask(__name__)

    SESSION_SECRET_KEY = "session_secret"
    SECRET_FILE_PATH = Path("../.flask_secret")
    try:
        # Read secret from the secret file
        with SECRET_FILE_PATH.open("r") as secret_file:
            app.secret_key = secret_file.read()
    except FileNotFoundError:
        # Secret file doesn't exist yet? Let's write a cryptographically secure code in a new file
        with SECRET_FILE_PATH.open("w") as secret_file:
            app.secret_key = secrets.token_hex(32)
            secret_file.write(app.secret_key)

    # Load config values from the config.ini config file
    config_ini = ConfigParser()
    config_ini.read("config.ini")

    if not config_ini:
        raise Exception("Config file not found. Please create a config.ini file in the project folder.")

    SERVER_NAME = config_ini["general"].get("SERVER_NAME")
    if not SERVER_NAME:
        print("SERVER_NAME not found in config.ini's general section. Using localhost:5000.")
        SERVER_NAME = "http://localhost:5000"

    if not config_ini["email"].get("SENDGRID_API_KEY"):
        raise Exception("SENDGRID_API_KEY not found in config.ini's email section.")

    if not config_ini["email"].get("FROM_EMAIL"):
        raise Exception("FROM_EMAIL not found in config.ini's email section'.")

    app.config.update(
        # Flask config values
        SESSION_COOKIE_SAMESITE="Lax" if app.config["DEBUG"] else "None",
        SESSION_COOKIE_SECURE=not app.config["DEBUG"],
        REMEMBER_COOKIE_SECURE=not app.config["DEBUG"],
        SESSION_PERMANENT=True,
        SESSION_DURATION=timedelta(days=31),
        # Custom config values
        APP_NAME="Your App",
        SERVER_NAME=SERVER_NAME,
        SESSION_SECRET_KEY=SESSION_SECRET_KEY,
        SENDGRID_API_KEY=config_ini["email"]["SENDGRID_API_KEY"],
        FROM_EMAIL=config_ini["email"]["FROM_EMAIL"],
        DATA_DIR=Path("data"),
    )
    if config_update:
        app.config.update(config_update)

    # Enable static file serving from the "static" folder
    app.static_folder = "static"

    with app.app_context():
        from blueprints.auth import auth
        from blueprints.email import email
        from blueprints.main import main

    app.register_blueprint(auth)
    app.register_blueprint(email)
    app.register_blueprint(main)
    return app


if __name__ == "__main__":
    main_app = create_app()

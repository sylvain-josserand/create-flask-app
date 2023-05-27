import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask

from views.auth import auth
from views.main import main

app = Flask(__name__)
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


app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    REMEMBER_COOKIE_SECURE=True,
    SESSION_DURATION=timedelta(days=14),
)
app.register_blueprint(auth)
app.register_blueprint(main)

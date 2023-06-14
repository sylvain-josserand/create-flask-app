import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, session, g, flash

from blueprints.auth import auth
from blueprints.main import main

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

app.config.update(
    # Flask config values
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    REMEMBER_COOKIE_SECURE=True,
    SESSION_PERMANENT=True,
    SESSION_DURATION=timedelta(days=31),
    # Custom config values
    SESSION_SECRET_KEY=SESSION_SECRET_KEY,
)
app.register_blueprint(auth)
app.register_blueprint(main)


@app.before_request
def create_guest_session_if_needed():
    from db.models.auth.session import Session
    from db.models.auth.user import User

    user = None

    if SESSION_SECRET_KEY in session:
        # Returns None if session_secret is invalid or expired
        user = User.get_by_session_secret(session[SESSION_SECRET_KEY])

    if user is None:
        if SESSION_SECRET_KEY in session:
            # Session is expired
            flash("Your session has expired. When using the app as guest, remember to sign in to save your work.")
        user = User.create_guest()
        db_session = Session.create(user.id)
        session[SESSION_SECRET_KEY] = db_session.secret
    g.user = user

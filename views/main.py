import configparser
import functools

from flask import render_template, session, url_for, redirect, flash, Blueprint

from db.models.auth.account import Account
from db.models.auth.session import Session
from db.models.auth.user import User

main = Blueprint("main", __name__, template_folder="templates")


@main.route("/")
def index():
    current_session = None
    if "session_secret" in session:
        # Get current session
        current_session = Session.get_unexpired(secret=session["session_secret"])

        if current_session is None:
            # Delete session secret from the session
            del session["session_secret"]
            # Redirect to the login page
            flash(
                "Your session has expired. Please log in again, create a new account, or start from scratch as a guest."
            )
            return redirect(url_for("auth.login"))

        # Get current user
        current_user = User.get_by_id(current_session.user_id)

    if current_session is None:
        # Create guest user
        current_user = User.create_guest()
        # Create new account
        current_account = Account.create(name="guest")
        # Link user to account as admin
        current_account.add_user(current_user, role="admin")
        # Create new session
        current_session = Session.create(user_id=current_user.id)
        session["session_secret"] = current_session.secret

    return render_template("index.html", user=current_user)

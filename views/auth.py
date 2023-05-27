import functools
import sqlite3

from flask import session, redirect, url_for, request, render_template, flash, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

from db.models.auth.user import User

auth = Blueprint("auth", __name__, template_folder="templates")


def login_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if "user" in session:
            return func(*args, **kwargs)
        return redirect(url_for("auth.login", next=url_for(func.__name__)))

    return decorated_function


@auth.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        errors = []

        email = request.form.get("email")
        if not email:
            errors.append("Please enter an email")

        name = request.form.get("name")
        if not name:
            errors.append("Please enter a name")

        password = request.form.get("password")
        if not password:
            errors.append("Please enter a password in the first password field")

        password2 = request.form.get("password2")
        if not password2:
            errors.append("Please enter a password in the second password field")

        password = request.form.get("password")
        password2 = request.form.get("password2")
        if password != password2:
            errors.append("Passwords don't match. Please try again")

        if not errors:
            con, cur = User.connect_to_db()

            user_exists = False
            for _ in cur.execute("SELECT email FROM user WHERE email = ?", (email,)):
                user_exists = True

            if user_exists:
                errors.append("A user with that email already exists. Please use another email or log in if it's you")
            else:
                # Actually create the user
                hashed_password = generate_password_hash(password)
                cur.execute(
                    """INSERT INTO user(email, name, password_hash)
                    VALUES (?, ?, ?)""",
                    (
                        email,
                        name,
                        hashed_password,
                    ),
                )
                con.commit()
                session["user"] = {"email": email, "name": name}
                return redirect(request.args.get("next", "/"))

        # Show errors and render the signup form again
        for error_message in errors:
            flash(error_message)
        return render_template("auth/signup.html")
    return render_template("auth/signup.html")


@auth.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        errors = []
        email = request.form.get("email")
        if not email:
            errors.append("Please enter an email")

        password = request.form.get("password")
        if not password:
            errors.append("Please enter a password")

        if not errors:
            con = sqlite3.connect(MAIN_DB_FILE_NAME)
            cur = con.cursor()

            user = None
            hashed_password = None
            for (
                name,
                hashed_password,
            ) in cur.execute("SELECT name, password FROM user WHERE email = ?", (email,)):
                user = {"email": email, "name": name}

            if user:
                if check_password_hash(hashed_password, password):
                    session["user"] = user
                    return redirect(request.args.get("next", "/"))
                else:
                    errors.append("Incorrect password")
            else:
                errors.append("No such user")
        for error_message in errors:
            flash(error_message)
    return render_template("auth/login.html")


@auth.route("/logout", methods=["GET"])
def logout():
    session.pop("user", None)
    return redirect(request.args.get("next", "/"))

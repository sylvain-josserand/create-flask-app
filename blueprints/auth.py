from flask import current_app, session, redirect, request, render_template, flash, Blueprint, g
from werkzeug.security import generate_password_hash, check_password_hash

from db.models.auth.user import User

auth = Blueprint("auth", __name__, template_folder="templates")


@auth.route("/signup", methods=["POST", "GET"])
def signup():
    SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]
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

        if password and password2 and (password != password2):
            password = password2 = None
            errors.append("Passwords don't match. Please try again")

        if not errors:
            con = User.connect_to_db()

            user_exists = False
            with con:
                for _ in con.execute("SELECT email FROM user WHERE email = ?", (email,)):
                    user_exists = True

            if user_exists:
                errors.append("A user with that email already exists. Please use another email or log in if it's you")
            else:
                # Actually create the user
                hashed_password = generate_password_hash(password)
                with con:
                    cur = con.execute(
                        """INSERT INTO user(email, name, password_hash)
                        VALUES (?, ?, ?)""",
                        (
                            email,
                            name,
                            hashed_password,
                        ),
                    )

                    # Update the current guest session with the new user, make sure the session doesn't belong to a user already
                    con.execute(
                        """UPDATE session
                           SET user_id = ?
                           WHERE session.secret = ?""",
                        (
                            cur.lastrowid,
                            session[SESSION_SECRET_KEY],
                        ),
                    )
                con.close()
                return redirect(request.args.get("next", "/"))

        # Show errors and render the signup form again
        for error_message in errors:
            flash(error_message)
        return render_template("auth/signup.html", email=email, name=name, password=password, password2=password2)
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
            user, is_password_ok = User.login(email, password)

            if not user:
                errors.append("No such user")
            elif not is_password_ok:
                errors.append("Incorrect password")

        for error_message in errors:
            flash(error_message)
        if errors:
            return render_template("auth/login.html", email=email, password=password)
        else:
            return redirect(request.args.get("next", "/"))
    return render_template("auth/login.html")


@auth.route("/logout", methods=["GET"])
def logout():
    SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]
    session.pop(SESSION_SECRET_KEY, None)
    if g.user:
        g.user.logout()
        g.user = None
    return redirect(request.args.get("next", "/"))

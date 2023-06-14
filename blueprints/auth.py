from flask import current_app, session, redirect, request, render_template, flash, Blueprint, g, url_for
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
                # Actually update the current guest user with the actual user data
                hashed_password = generate_password_hash(password)
                with con:
                    con.execute(
                        """UPDATE user SET email = ?, name = ?, password_hash = ? WHERE id = ?""",
                        (
                            email,
                            name,
                            hashed_password,
                            g.user.id,
                        ),
                    )
                # No need to update the session since the user is already logged in
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


@auth.route("/profile", methods=["GET"])
def profile():
    return render_template("auth/profile.html")


@auth.route("/user/update", methods=["POST"])
def user_update():
    g.user.update(email=request.form.get("email"), name=request.form.get("name"))
    return redirect(url_for("auth.profile"))


@auth.route("/user/change_password", methods=["POST"])
def user_update_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    new_password2 = request.form.get("new_password2")

    errors = []

    # Check old password
    if old_password:
        if check_password_hash(g.user.password_hash, old_password):
            pass  # Old password is present and correct
        else:
            errors.append("Old password is incorrect")
    else:
        errors.append("Please enter your old password")

    # Check new passwords
    if new_password and new_password2 and new_password == new_password2:
        pass  # New passwords are present and match
    elif not new_password:
        errors.append("Please enter a new password")
    elif not new_password2:
        errors.append("Please enter your new password again")
    elif new_password != new_password2:
        errors.append("New passwords don't match")
    else:
        errors.append("Unknown error. Please check your inputs and try again")

    if errors:
        for error_message in errors:
            flash(error_message)
    else:
        g.user.update(password_hash=generate_password_hash(new_password))
    return redirect(url_for("auth.profile"))


@auth.route("/user/delete", methods=["POST"])
def user_delete():
    g.user.logout()
    g.user.delete()
    return redirect(url_for("main.index"))

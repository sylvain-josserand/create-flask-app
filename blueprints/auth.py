from datetime import datetime

from flask import current_app, session, redirect, request, render_template, flash, Blueprint, g, url_for
from werkzeug.security import check_password_hash

from blueprints.email import send_email
from db.models.auth.session import Session
from db.models.auth.user import User
from db.models.auth.user_account import UserAccount
from db.models.auth.invitation import Invitation

auth = Blueprint("auth", __name__, template_folder="templates")


@auth.route("/signup", methods=["POST", "GET"])
def signup():
    invitation_secret = request.args.get("invitation_secret", request.form.get("invitation_secret"))
    if request.method == "POST":
        if g.user.email:
            # User is already logged in with a non-guest account, let's log them out first
            # This could happen and cause trouble when accepting an invitation while logged in
            g.user.logout()
            # And create a new guest user
            g.user = User.create_guest_and_login()
        errors = []

        email = request.form.get("email")
        if not email:
            errors.append("Please enter a valid email address")

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

        invitation = None
        if invitation_secret:
            invitation = Invitation.get_by_secret(invitation_secret)

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
                hashed_password = User.generate_password_hash(password)
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
                # But don't forget to update g.user
                g.user = User.get_by_id(g.user.id)
                flash("Account created. Welcome! 🎉")

                if invitation_secret and invitation:
                    invitation.accept(g.user)

                return redirect(request.args.get("next", "/"))

        # Show errors and render the signup form again
        for error_message in errors:
            flash(error_message)
        return render_template("auth/signup.html", email=email, name=name, password=password, password2=password2), 401

    if invitation_secret:
        return Invitation.render_template("auth/signup.html", invitation_secret=invitation_secret)
    return render_template("auth/signup.html")


@auth.route("/login", methods=["POST", "GET"])
def login():
    invitation_secret = request.args.get("invitation_secret", request.form.get("invitation_secret"))

    if request.method == "POST":
        errors = []
        email = request.form.get("email")
        if not email:
            errors.append("Please enter a valid email address")

        password = request.form.get("password")
        if not password:
            errors.append("Please enter a password")

        invitation = None
        if invitation_secret:
            invitation = Invitation.get_by_secret(invitation_secret)

        user = None
        if not errors:
            user, is_password_ok = User.login(email, password)

            if not user:
                errors.append("No such user")
            elif not is_password_ok:
                errors.append("Incorrect password")

        for error_message in errors:
            flash(error_message)
        if errors:
            return render_template("auth/login.html", email=email, password=password), 401
        else:
            if invitation_secret and invitation:
                invitation.accept(user)

            flash("Logged in. Welcome back! 😊")
            return redirect(request.args.get("next", "/"))
    if invitation_secret:
        return Invitation.render_template("auth/login.html", invitation_secret=invitation_secret)
    return render_template("auth/login.html")


@auth.route("/logout", methods=["GET"])
def logout():
    SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]
    session.pop(SESSION_SECRET_KEY, None)
    if g.user:
        g.user.logout()
        g.user = None
    flash("Logged out. Bye! 👋")
    return redirect(request.args.get("next", "/"))


@auth.route("/account", methods=["GET"])
def account():
    if g.user.email:
        # Only display account to non-guest users
        return render_template("auth/account.html")
    return redirect(url_for("auth.login", next=url_for("auth.account")))


@auth.route("/user/update", methods=["POST"])
def user_update():
    g.user.update(email=request.form.get("email"), name=request.form.get("name"))
    flash("User updated successfully! 🎉")
    return redirect(url_for("auth.account"))


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
        g.user.update(password_hash=User.generate_password_hash(new_password))
        flash("Password updated successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/user/delete", methods=["POST"])
def user_delete():
    g.user.logout()
    g.user.delete()
    flash("User deleted successfully. Farewell! 👋")
    return redirect(url_for("main.index"))


@auth.route("/account/<int:account_id>/update", methods=["POST"])
def account_update(account_id):
    from db.models.auth.account import Account
    from db.models.auth.user_account import UserAccount

    user_account = UserAccount.select(user_id=g.user.id, account_id=account_id, role="admin")
    if not user_account:
        flash("You don't have permission to edit this account")
        return redirect(url_for("auth.account"))

    Account.update_by_id(
        account_id,
        name=request.form.get("name"),
    )
    flash("Account updated successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/account/<int:account_id>/delete", methods=["POST"])
def account_delete(account_id):
    from db.models.auth.account import Account

    user_account_set = UserAccount.select(user_id=g.user.id, account_id=account_id)

    if not user_account_set:
        flash("You are not a member of this account. You must be a member with admin rights to delete an account")
        return redirect(url_for("auth.account"))

    user_account = user_account_set[0]
    if user_account.role != "admin":
        flash("You don't have permission to edit this account. You must be admin to delete an account")
        return redirect(url_for("auth.account"))

    constraints = []

    # Make sure each user has at least one account left
    user_account_count = len(UserAccount.select(user_id=g.user.id))
    if user_account_count <= 1:
        constraints.append("You can't delete this account because you would have no accounts left")

    if constraints:
        for constraint in constraints:
            flash(constraint)
        return redirect(url_for("auth.account"))

    Account.delete_by_id(account_id)
    flash("Account deleted successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/user_account/<int:user_account_id>/update", methods=["POST"])
def user_account_update(user_account_id):
    """Mainly to change role of user on a given account"""
    from db.models.auth.user_account import UserAccount

    user_account = UserAccount.get_by_id(user_account_id)
    if not user_account:
        flash("User account to be changed not found")
        return redirect(url_for("auth.account"))

    account_id = user_account.account_id

    # Check if current user has permission to edit this account
    admin_user_account = UserAccount.select(account_id=account_id, user_id=g.user.id, role="admin")
    if not admin_user_account:
        flash("You don't have permission to edit this account")
        return redirect(url_for("auth.account"))

    if request.form.get("role") not in UserAccount.role_choices:
        flash(f"Invalid role. Should be one of {', '.join(UserAccount.role_choices)}")
        return redirect(url_for("auth.account"))

    # Make sure there is at least one admin
    if user_account.role == "admin" and request.form.get("role") != "admin":
        if len(UserAccount.select(account_id=account_id, role="admin")) <= 1:
            if user_account.user_id == g.user.id:
                flash("You can't remove your admin rights because you are the only admin")
            else:
                flash("You can't remove this user's admin rights because it is the last admin")
            return redirect(url_for("auth.account"))

    UserAccount.update_by_id(
        user_account.id,
        role=request.form.get("role"),
    )
    flash("User account updated successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/user_account/<int:user_account_id>/delete", methods=["POST"])
def user_account_delete(user_account_id):
    from db.models.auth.user_account import UserAccount

    user_account = UserAccount.get_by_id(user_account_id)
    if not user_account:
        flash("User account to be deleted not found")
        return redirect(url_for("auth.account"))

    # Make sure there is at least one admin left in the group at all times, to prevent lockout
    admin_count = len(UserAccount.select(account_id=user_account.account_id, role="admin"))

    if user_account.role == "admin" and admin_count <= 1:
        flash("You can't remove this user from this account because there would be no admins left")
        return redirect(url_for("auth.account"))

    user_account.delete()
    flash("User account deleted successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/account/<int:account_id>/invite", methods=["POST"])
def account_invite(account_id):
    """Invite a user to join an account"""
    # Check that the inviting user is an admin of the account
    from db.models.auth.user_account import UserAccount

    if not UserAccount.select(user_id=g.user.id, account_id=account_id, role="admin"):
        flash("You don't have permission to invite users to this account")
        return redirect(url_for("auth.account"))

    email = request.form.get("email")
    if not email:
        flash("You must enter an email address")
        return redirect(url_for("auth.account"))

    role = request.form.get("role")
    if role not in UserAccount.role_choices:
        flash(f"Invalid role. Should be one of {', '.join(UserAccount.role_choices)}")
        return redirect(url_for("auth.account"))

    # Insert a new invite into the invitation database table
    invitation_id = Invitation.insert(account_id=account_id, email=email, created_by=g.user.id, role=role)
    invitation = Invitation.get_by_id(invitation_id)

    APP_NAME = current_app.config["APP_NAME"]

    # Send an email to the user with a link to accept the invitation
    send_email(
        to=email,
        subject=f"You have been invited to join an account on {APP_NAME}",
        html_content=render_template(
            "auth/invitation_email.html",
            invitation=invitation,
            app_name=APP_NAME,
        ),
    )
    flash("Invitation sent successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/invitation/<secret>", methods=["GET"])
def invitation(secret):
    invitation = Invitation.get_by_secret(secret)
    if not invitation:
        flash("Invalid invitation")
        return redirect(url_for("auth.account"))

    return render_template(
        "auth/invitation.html",
        invitation=invitation,
        from_email=current_app.config["FROM_EMAIL"],
    )


@auth.route("/invitation_accept", methods=["POST"])
def invitation_accept():
    invitation_secret = request.form.get("invitation_secret")

    invitation = Invitation.get_by_secret(invitation_secret)
    if not invitation:
        flash("Invalid invitation")
        return redirect(url_for("auth.account"))

    # Check if the user already has an account
    from db.models.auth.user import User

    invited_users = User.select(email=invitation.email)
    if not invited_users:
        flash("You must create an account first")
        return redirect(url_for("auth.signup", invitation_secret=invitation_secret))

    # Check if the user is not already a member of the account
    from db.models.auth.user_account import UserAccount

    user_account = UserAccount.select(
        user_id=invited_users[0].id,
        account_id=invitation.account_id,
    )
    if user_account:
        flash("There is already such a member in this account")
        return redirect(url_for("auth.account"))

    # From here on, the user has an account
    invited_user = invited_users[0]
    if g.user.id == invited_user.id:
        # The invited user is the current user: accept the invitation by adding the user to the account
        from db.models.auth.user_account import UserAccount

        UserAccount.insert(user_id=invited_user.id, account_id=invitation.account_id, role=invitation.role)

        invitation.update(status="accepted")
        flash("Invitation accepted. Welcome to the team! 🎉")

        return redirect(url_for("auth.account"))

    # The invited user is not the current user: log out the current user and log in the invited user
    g.user.logout()
    flash("You have been logged out. Please log in with the invited account to accept the invitation.")
    return redirect(url_for("auth.login", invitation_secret=invitation_secret))


@auth.route("/invitation_decline", methods=["POST"])
def invitation_decline():
    invitation_secret = request.form.get("invitation_secret")

    invitation = Invitation.get_by_secret(invitation_secret)

    if not invitation:
        flash("Invalid invitation")
        return redirect(url_for("auth.account"))

    # Set the invitation status to declined
    invitation.update(status="declined")
    flash("Invitation successfully declined 🎉")

    return redirect(url_for("auth.account"))


@auth.route("/account_create", methods=["POST"])
def account_create():
    from db.models.auth.account import Account
    from db.models.auth.user_account import UserAccount

    account = Account.insert(name=request.form.get("name"))
    UserAccount.insert(account_id=account.id, user_id=g.user.id, role="admin")
    flash("Account created successfully! 🎉")
    return redirect(url_for("auth.account"))


@auth.route("/invitation_delete/<int:invitation_id>", methods=["POST"])
def invitation_delete(invitation_id):
    if not invitation_id:
        flash("No invitation ID")
        return redirect(url_for("auth.account"))

    invitation = Invitation.get_by_id(invitation_id)
    if not invitation:
        flash("Non-existent invitation ID")
        return redirect(url_for("auth.account"))

    from db.models.auth.account import Account

    account = Account.get_by_id(invitation.account_id)

    # Check that the inviting user is an admin of the account
    from db.models.auth.user_account import UserAccount

    if not UserAccount.select(user_id=g.user.id, account_id=account.id, role="admin"):
        flash("You don't have permission to delete this invitation")
        return redirect(url_for("auth.account"))

    Invitation.delete_by_id(invitation_id)
    flash("Invitation deleted successfully! 🎉")
    return redirect(url_for("auth.account"))


# Run this function before every request
@auth.before_app_request
def create_guest_session_if_needed():
    from db.models.auth.user import User

    SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]

    user = None

    if SESSION_SECRET_KEY in session:
        # Returns None if session_secret is invalid or expired
        user = User.get_by_session_secret(session[SESSION_SECRET_KEY])

    if user is None:
        if SESSION_SECRET_KEY in session:
            # Session is expired
            flash("Your session has expired. When using the app as guest, remember to sign in to save your work.")

        user = User.create_guest_and_login()

    g.user = user


@auth.route("/forgotten_password", methods=["GET", "POST"])
def forgotten_password():
    if request.method == "GET":
        return render_template("auth/forgotten_password.html")

    email = request.form.get("email")
    if not email:
        flash("Please enter your email")
        return redirect(url_for("auth.forgotten_password"))

    from db.models.auth.user import User

    user = User.select(email=email)
    if not user:
        flash("No user with this email")
        return redirect(url_for("auth.forgotten_password"))

    # Create a session for this user in the DB
    session_id = Session.insert(user_id=user[0].id)
    session = Session.get_by_id(session_id)

    user = user[0]
    send_email(
        to=user.email,
        subject="Reset your password",
        html_content=render_template(
            "auth/reset_password_email.html", app_name=current_app.config["APP_NAME"], secret=session.secret
        ),
    )

    flash("Email sent. Please check your inbox.")
    return redirect(url_for("auth.login"))


@auth.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    secret = request.args.get("secret", request.form.get("secret"))
    session = Session.select_one(secret=secret)
    if not session:
        flash("Invalid reset password link")
        return redirect(url_for("auth.login"))

    if session.expires < datetime.now().isoformat():
        flash("Reset password link expired")
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("auth/reset_password.html", session=session)

    errors = []
    password = request.form.get("password")
    if not password:
        errors.append("Please enter a password")

    password2 = request.form.get("password2")
    if not password2:
        errors.append("Please confirm your password")

    if password != password2:
        errors.append("Passwords don't match")

    if errors:
        for error in errors:
            flash(error)
        return render_template("auth/reset_password.html", session=session), 400

    from db.models.auth.user import User

    # Update the user's password
    User.update_by_id(session.user.id, password_hash=User.generate_password_hash(password))

    user, password_ok = session.user.login(session.user.email, password)
    if not password_ok:
        flash("Invalid password")
        return render_template("auth/reset_password.html", session=session)
    flash("Password updated successfully! 🎉")
    return redirect(url_for("main.index"))

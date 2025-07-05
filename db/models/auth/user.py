import secrets
from datetime import datetime

from flask import current_app, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from db.models.auth.auth_model import AuthModel


class User(AuthModel):
    table_name = "user"
    fields = ("id", "name", "email", "password_hash", "created", "last_login", "current_account_id")

    @property
    def current_account(self):
        from db.models.auth.account import Account

        return Account.get_by_id(self.current_account_id)

    @classmethod
    def generate_password_hash(cls, password):
        # Tests run slow with default hash algorithm PBKDF2
        # We're using scrypt here so that tests run faster, and our app is still secure (compared to sha256)
        return generate_password_hash(password, method="scrypt")

    @classmethod
    def insert(cls, name, email, password):
        from db.models.auth.account import Account
        from db.models.auth.user_account import UserAccount

        con = cls.connect_to_db()
        if password is None:
            password_hash = None
        else:
            password_hash = cls.generate_password_hash(password)

        # Create a default personal account for the user
        account_id = Account.insert("Personal")

        with con:
            cur = con.execute(
                f'INSERT INTO {cls.table_name} ("name", "email", "password_hash", "current_account_id") VALUES (?, ?, ?, ?)',
                (
                    name,
                    email,
                    password_hash,
                    account_id,
                ),
            )
            user_id = cur.lastrowid
        con.close()

        # Link the user to the default personal account
        UserAccount.insert(user_id=user_id, account_id=account_id, role="admin")
        return user_id

    @classmethod
    def get_by_session_secret(cls, secret):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {cls.comma_separated_fields()}
                    FROM user 
                    INNER JOIN session ON session.user_id = user.id
                    WHERE session.secret = ? AND session.expires > ?""",
                (secret, datetime.now()),
            )
        row = cur.fetchone()
        con.close()
        if row is None:
            return None
        return cls(**row)

    @classmethod
    def login(cls, email, password):
        """Returns (user, is_password_ok)"""
        from db.models.auth.session import Session

        SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]

        user = User.select_one(email=email)
        if user is None:
            return None, False

        if check_password_hash(user.password_hash, password):
            # Update the db session to point to the logged-in user, but only if it's a guest session!
            db_session = Session.select_one_unexpired(secret=session[SESSION_SECRET_KEY])
            if db_session:
                if db_session.user.email is None:
                    # Update the guest session to point to the logged-in user
                    db_session.update(user_id=user.id)
                else:  # Logged in with a different user
                    g.user.logout()
                    # Create a new session
                    db_session_id = Session.insert(user_id=user.id)
                    db_session = Session.get_by_id(db_session_id)
                    session[SESSION_SECRET_KEY] = db_session.secret
                    g.user = user
                    g.account = user.current_account
            else:
                # Low chance of happening because we create guest session by default
                Session.insert(user_id=user.id)

            # Update the last login time
            user.update(last_login=datetime.now())

            return user, True
        return user, False

    def logout(self):
        """Expire all the sessions for this user."""
        SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]
        now = datetime.now()

        con = self.connect_to_db()

        with con:
            con.execute(
                "UPDATE session SET expires = ? WHERE user_id = ? AND expires > ?",
                (
                    now,
                    self.id,
                    now,
                ),
            )
        con.close()
        session.pop(SESSION_SECRET_KEY, None)

    @property
    def account_set(self):
        from db.models.auth.account import Account

        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"SELECT {Account.comma_separated_fields()} FROM user_account "
                f"INNER JOIN account ON account.id = user_account.account_id "
                f"WHERE user_account.user_id = ?",
                (self.id,),
            )
            for row in cur.fetchall():
                yield Account(**row)
        con.close()

    @property
    def user_account_set(self):
        from db.models.auth.user_account import UserAccount

        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"SELECT {UserAccount.comma_separated_fields()} FROM user_account WHERE user_account.user_id = ?",
                (self.id,),
            )
            for row in cur.fetchall():
                yield UserAccount(**row)
        con.close()

    @property
    def zip_account_set(self):
        return zip(self.account_set, self.user_account_set)

    @classmethod
    def create_guest_and_login(cls):
        from db.models.auth.session import Session

        user_id = cls.insert(name="Guest", email=None, password=None)

        SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]
        db_session_id = Session.insert(user_id)
        db_session = Session.get_by_id(db_session_id)
        user = User.get_by_id(user_id)
        session[SESSION_SECRET_KEY] = db_session.secret
        return user

import secrets
from datetime import datetime

from flask import current_app, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from db.models.auth.auth_model import AuthModel


class User(AuthModel):
    table_name = "user"
    fields = ("id", "name", "email", "password_hash", "created", "last_login")

    @classmethod
    def insert(cls, name, email, password):
        con = cls.connect_to_db()
        if password is None:
            password_hash = None
        else:
            password_hash = generate_password_hash(password, method="scrypt")

        with con:
            cur = con.execute(
                f'INSERT INTO {cls.table_name} ("name", "email", "password_hash") VALUES (?, ?, ?)',
                (
                    name,
                    email,
                    password_hash,
                ),
            )
            user_id = cur.lastrowid
            # Create a personal account for the user
            cur = con.execute(
                "INSERT INTO account (account_db_file_name, name) VALUES (?, ?)",
                (secrets.token_hex(16) + ".db", "Personal"),
            )
            account_id = cur.lastrowid
            # Link the user to the account
            con.execute(
                "INSERT INTO user_account (user_id, account_id, role) VALUES (?, ?, ?)", (user_id, account_id, "admin")
            )
        con.close()
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
        SESSION_SECRET_KEY = current_app.config["SESSION_SECRET_KEY"]

        con = User.connect_to_db()

        with con:
            cur = con.execute(f"SELECT {cls.comma_separated_fields()} FROM user WHERE email = ?", (email,))
            result = cur.fetchone()
            if result:
                user = cls(**result)
            else:
                return None, False

        if check_password_hash(user.password_hash, password):
            # Update the session to point to the logged-in user
            with con:
                con.execute("UPDATE session SET user_id = ? WHERE secret = ?", (user.id, session[SESSION_SECRET_KEY]))
                con.execute("UPDATE user SET last_login = ? WHERE id = ?", (datetime.now(), user.id))
            con.commit()
            g.user = user
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
        db_session = Session.insert(user_id)
        user = User.get_by_id(user_id)
        session[SESSION_SECRET_KEY] = db_session.secret
        return user

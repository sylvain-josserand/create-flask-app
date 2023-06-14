from datetime import datetime

from flask import current_app, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from db.models.auth.auth_model import AuthModel


class User(AuthModel):
    table_name = "user"
    fields = ("id", "name", "email", "password_hash", "created", "last_login")

    def __init__(self, id, name, email, password_hash, created, last_login):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created = created
        self.last_login = last_login

    @classmethod
    def create(cls, name, email, password):
        con = cls.connect_to_db()
        if password is None:
            password_hash = None
        else:
            password_hash = generate_password_hash(password)

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
        con.close()
        return cls.get_by_id(user_id)

    @classmethod
    def create_guest(cls):
        return cls.create(name="Guest", email=None, password=None)

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
            con.commit()
            g.user = user
            return user, True
        return user, False

    def logout(self):
        """Expire all the sessions for this user."""
        con = self.connect_to_db()
        with con:
            now = datetime.now()
            con.execute(
                "UPDATE session SET expires = ? WHERE user_id = ? AND expires > ?",
                (
                    now,
                    self.id,
                    now,
                ),
            )
        con.close()
        session.pop(current_app.config["SESSION_SECRET_KEY"], None)
        g.user = None

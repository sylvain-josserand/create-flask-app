import secrets
from datetime import datetime

import flask

from db.models.auth.auth_model import AuthModel

app = flask.current_app


class Session(AuthModel):
    table_name = "session"
    fields = ("id", "secret", "user_id", "created", "expires")

    @classmethod
    def insert(cls, user_id):
        con = cls.connect_to_db()
        expires = datetime.now() + app.config["SESSION_DURATION"]

        with con:
            cur = con.execute(
                f"INSERT INTO {cls.table_name} (user_id, secret, expires) VALUES (?, ?, ?)",
                (
                    user_id,
                    Session.generate_secret(),
                    expires,
                ),
            )
        con.close()
        return cur.lastrowid

    @classmethod
    def select_one_unexpired(cls, secret):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {cls.comma_separated_fields()}
                    FROM {cls.table_name}
                    WHERE secret = ? AND expires > ?""",
                (secret, datetime.now()),
            )
        row = cur.fetchone()
        con.close()
        if row is None:
            return None
        return cls(**row)

    @property
    def user(self):
        from db.models.auth.user import User

        return User.get_by_id(self.user_id)

    @classmethod
    def generate_secret(cls):
        return secrets.token_hex(64)

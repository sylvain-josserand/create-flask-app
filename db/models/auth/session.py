import secrets
from datetime import datetime

import flask

from db.connection import connect_to_db
from db.models.auth.auth_model import AuthModel

app = flask.current_app


class Session(AuthModel):
    table_name = "session"
    fields = ("id", "secret", "user_id", "created", "expires")

    def __init__(self, id, secret, user_id, created, expires):
        self.id = id
        self.secret = secret
        self.user_id = user_id
        self.created = created
        self.expires = expires

    @classmethod
    def create(cls, user_id):
        con, cur = cls.connect_to_db()
        secret = secrets.token_hex(64)
        expires = datetime.now() + app.config["SESSION_DURATION"]

        cur.execute(
            f"INSERT INTO {cls.table_name} (user_id, secret, expires) VALUES (?, ?, ?)",
            (
                user_id,
                secret,
                expires,
            ),
        )
        con.commit()
        con.close()
        return cls.get_by_id(cur.lastrowid)

    @classmethod
    def get_unexpired(cls, secret):
        con, cur = cls.connect_to_db()
        cur.execute(
            f"SELECT {cls.comma_separated_fields()} FROM {cls.table_name} WHERE secret = ? AND expires > ?",
            (
                secret,
                datetime.now(),
            ),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return cls(**dict(zip(cls.fields, row)))

import secrets
from datetime import datetime

import flask

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
        con = cls.connect_to_db()
        secret = secrets.token_hex(64)
        expires = datetime.now() + app.config["SESSION_DURATION"]

        with con:
            cur = con.execute(
                f"INSERT INTO {cls.table_name} (user_id, secret, expires) VALUES (?, ?, ?)",
                (
                    user_id,
                    secret,
                    expires,
                ),
            )
        con.close()
        return cls.get_by_id(cur.lastrowid)

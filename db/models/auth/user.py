import secrets

from werkzeug.security import generate_password_hash

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
        con, cur = cls.connect_to_db()
        if password is None:
            password_hash = None
        else:
            password_hash = generate_password_hash(password)

        cur.execute(
            f'INSERT INTO {cls.table_name} ("name", "email", "password_hash") VALUES (?, ?, ?)',
            (
                name,
                email,
                password_hash,
            ),
        )
        user_id = cur.lastrowid
        con.commit()
        con.close()
        return cls.get_by_id(user_id)

    @classmethod
    def create_guest(cls):
        result = cls.create(name=secrets.token_hex(64), email=None, password=None)

        # Update user name to include user id
        con, cur = cls.connect_to_db()
        with con:
            cur.execute(f"UPDATE {cls.table_name} SET name = ? WHERE id = ?", (f"guest-{result.id}", result.id))
            con.commit()

        return cls.get_by_id(result.id)

    @classmethod
    def get_by_session_secret(cls, secret):
        con, cur = cls.connect_to_db()
        cur.execute(f"SELECT user_id FROM session WHERE secret = ?", (secret,))
        row = cur.fetchone()
        if row is None:
            return None
        return cls.get_by_id(row[0])

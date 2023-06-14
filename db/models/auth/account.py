import secrets
from pathlib import Path

from db.models.auth.auth_model import AuthModel


class Account(AuthModel):
    table_name = "account"
    fields = ("id", "account_db_file_name", "name")

    def __init__(self, id, account_db_file_name, name):
        self.id = id
        self.account_db_file_name = (
            account_db_file_name  # account_db_file_name is the name of the database file for auth
        )
        self.name = name

    @classmethod
    def create(cls, name):
        secret = secrets.token_hex(16)
        account_db_file_name = Path("data", "accounts", *secret[:6], secret + ".db")
        account_db_file_name.parent.mkdir(parents=True, exist_ok=True)

        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"INSERT INTO {cls.table_name} (name, account_db_file_name) VALUES (?, ?)",
                (name, account_db_file_name.as_posix()),
            )
            account_id = cur.lastrowid
        con.close()
        return cls.get_by_id(account_id)

    def add_user(self, user, role):
        """Add a user to this account."""
        con = self.connect_to_db()
        with con:
            con.execute(
                "INSERT INTO user_account (account_id, user_id, role) VALUES (?, ?, ?)", (self.id, user.id, role)
            )
        con.close()

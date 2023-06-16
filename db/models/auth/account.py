import secrets
from pathlib import Path

from db.models.auth.auth_model import AuthModel


class Account(AuthModel):
    table_name = "account"
    fields = (
        "id",
        "account_db_file_name",  # account_db_file_name is the name of the database file for auth
        "name",
    )

    @property
    def user_account_set(self):
        """Return a set of user accounts that belong to this account."""
        from db.models.auth.user_account import UserAccount

        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {UserAccount.comma_separated_fields()}
                    FROM user_account
                    WHERE user_account.account_id = ?""",
                (self.id,),
            )
        return [UserAccount(**row) for row in cur.fetchall()]

    @property
    def user_set(self):
        """Return a set of users that belong to this account."""
        from db.models.auth.user import User

        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {User.comma_separated_fields()}
                    FROM user
                    INNER JOIN user_account ON user_account.user_id = user.id
                    WHERE user_account.account_id = ?""",
                (self.id,),
            )
        return [User(**row) for row in cur.fetchall()]

    @property
    def invitation_set(self):
        """Return a set of invitations that belong to this account."""
        from db.models.auth.invitation import Invitation

        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {Invitation.comma_separated_fields()}
                    FROM invitation
                    WHERE invitation.account_id = ?""",
                (self.id,),
            )
        return [Invitation(**row) for row in cur.fetchall()]

    @classmethod
    def insert(cls, name):
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

    def role(self, user_id):
        """Returns the role of the user in the account, or None if the user is not in the account."""
        from db.models.auth.user_account import UserAccount

        user_account = UserAccount.select(user_id=user_id, account_id=self.id)
        if user_account:
            return user_account[0].role
        return None

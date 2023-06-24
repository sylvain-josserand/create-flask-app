from db.models.auth.auth_model import AuthModel


class UserAccount(AuthModel):
    table_name = "user_account"
    fields = ("id", "user_id", "account_id", "role")

    @property
    def user(self):
        from db.models.auth.user import User

        return User.get_by_id(self.user_id)

    @classmethod
    def select_excluding_account(cls, exclude_account_id, user_id):
        """Return a list of UserAccount objects that are not associated with the given account."""
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"""SELECT {cls.comma_separated_fields()}
                    FROM {cls.table_name}
                    WHERE account_id != ? AND user_id = ?""",
                (exclude_account_id, user_id),
            )
        result = [cls(**row) for row in cur.fetchall()]
        con.close()
        return result

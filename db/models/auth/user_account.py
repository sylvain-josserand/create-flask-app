from db.models.auth.auth_model import AuthModel


class UserAccount(AuthModel):
    table_name = "user_account"
    fields = ("id", "user_id", "account_id", "role")

    @property
    def user(self):
        from db.models.auth.user import User

        return User.get_by_id(self.user_id)

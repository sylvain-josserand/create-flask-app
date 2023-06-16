from db.model import Model


class AuthModel(Model):
    role_choices = ("admin", "user", "read-only")
    db_file_name = "data/auth.db"

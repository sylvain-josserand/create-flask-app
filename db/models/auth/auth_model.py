from db.model import Model

from flask import current_app


class AuthModel(Model):
    role_choices = ("admin", "user", "read-only")
    db_file_name = current_app.config["DATA_DIR"] / "auth.db"

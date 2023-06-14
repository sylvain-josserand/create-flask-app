import sqlite3
from flask import current_app


class MyConnect(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.row_factory = sqlite3.Row
        # Only in debug mode
        if current_app and current_app.config["DEBUG"]:
            self.set_trace_callback(print)
        with self:
            self.execute("PRAGMA foreign_keys = ON")


def connect_to_db(db_file_name):
    return MyConnect(db_file_name)

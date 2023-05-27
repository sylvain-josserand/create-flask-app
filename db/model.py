from db.connection import connect_to_db


class Model:
    """Base class for all models. This class is not supposed to be instantiated directly.
    Inherit from this class and override the fields and table_name class attributes."""

    fields = []  # Override with your fields' names
    table_name = ""  # Override with your table's name
    db_file_name = None  # Override with the name of the database file

    @classmethod
    def comma_separated_fields(self):
        return ", ".join(self.fields)

    @classmethod
    def connect_to_db(cls):
        return connect_to_db(cls.db_file_name)

    @classmethod
    def get_by_id(cls, id):
        con, cur = cls.connect_to_db()
        cur.execute(
            f"SELECT {cls.comma_separated_fields()} FROM {cls.table_name} WHERE id = ?",
            (id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return cls(**dict(zip(cls.fields, row)))

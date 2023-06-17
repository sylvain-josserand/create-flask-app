from db.connection import connect_to_db


class Model:
    """Base class for all models. This class is not supposed to be instantiated directly.
    Inherit from this class and override the fields and table_name class attributes."""

    fields = []  # Override with your fields' names
    table_name = ""  # Override with your table's name
    db_file_name = None  # Override with the name of the database file
    id = None  # Need to have a unique instance identifier called "id"

    def __init__(self, **kwargs):
        for field in self.fields:
            setattr(self, field, kwargs.pop(field))
        if kwargs:
            raise TypeError(f"Unexpected arguments: {', '.join(kwargs.keys())}")

    @classmethod
    def comma_separated_fields(self):
        return ", ".join(".".join((self.table_name, field)) for field in self.fields)

    @classmethod
    def connect_to_db(cls):
        return connect_to_db(cls.db_file_name)

    @classmethod
    def insert(cls, **fields):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"INSERT INTO {cls.table_name} ({', '.join(fields.keys())}) VALUES ({', '.join('?' for _ in fields)})",
                tuple(fields.values()),
            )
        con.close()
        return cur.lastrowid

    @classmethod
    def select(cls, **kwargs):
        con = cls.connect_to_db()
        with con:
            if kwargs:
                cur = con.execute(
                    f"SELECT {cls.comma_separated_fields()} FROM {cls.table_name} WHERE {' AND '.join(f'{key} = ?' for key in kwargs.keys())}",
                    tuple(kwargs.values()),
                )
            else:
                cur = con.execute(f"SELECT {cls.comma_separated_fields()} FROM {cls.table_name}")

        rows = cur.fetchall()
        con.close()
        return [cls(**row) for row in rows]

    @classmethod
    def count(cls, **kwargs):
        con = cls.connect_to_db()
        with con:
            if kwargs:
                cur = con.execute(
                    f"SELECT COUNT(*) FROM {cls.table_name} WHERE {' AND '.join(f'{key} = ?' for key in kwargs.keys())}",
                    tuple(kwargs.values()),
                )
            else:
                cur = con.execute(f"SELECT COUNT(*) FROM {cls.table_name}")

        row = cur.fetchone()
        con.close()
        return row[0]

    @classmethod
    def get_by_id(cls, id):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"SELECT {cls.comma_separated_fields()} FROM {cls.table_name} WHERE id = ?",
                (id,),
            )
        row = cur.fetchone()
        con.close()
        if row is None:
            return None
        return cls(**row)

    @classmethod
    def update_by_id(cls, id, **fields):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(
                f"""UPDATE {cls.table_name} SET {', '.join(f'{key} = ?' for key in fields.keys())} WHERE id = ?""",
                (*fields.values(), id),
            )
        con.close()
        return cur.rowcount == 1

    @classmethod
    def delete_by_id(cls, id):
        con = cls.connect_to_db()
        with con:
            cur = con.execute(f"DELETE FROM {cls.table_name} WHERE id = ?", (id,))
        con.close()
        return cur.rowcount == 1

    def update(self, **fields):
        con = self.connect_to_db()
        with con:
            cur = con.execute(
                f"""UPDATE {self.table_name} SET {', '.join(f'{key} = ?' for key in fields.keys())} WHERE id = ?""",
                (*fields.values(), self.id),
            )
        con.close()
        return cur.rowcount == 1

    def delete(self):
        con = self.connect_to_db()
        with con:
            cur = con.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (self.id,))
        con.close()
        return cur.rowcount == 1

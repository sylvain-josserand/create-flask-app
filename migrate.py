import pathlib
import sqlite3
from operator import itemgetter
from time import perf_counter

from db.connection import connect_to_db
from db.models.auth.account import Account
from db.models.auth.auth_model import AuthModel


def build_migrations_list(subpath):
    migrations = []
    migration_path = pathlib.Path("migrations") / subpath

    for file in migration_path.iterdir():
        with file.open("r") as f:
            migrations.append((file.name, f.read()))

    # Sort migrations by alphabetical order: 00001_..., 00002_..., etc.
    migrations.sort(key=itemgetter(0))
    return migrations


def migrate(db_file_name, migrations):
    db_file_path = pathlib.Path(db_file_name).parent

    # Let's create the DB directory, if it doesn't already exist
    db_file_path.mkdir(parents=True, exist_ok=True)

    migrate_con = sqlite3.connect(db_file_name)
    migrate_cur = migrate_con.cursor()
    print(f"Creating table migrations on the {db_file_name} database, if not already there.")
    migrate_cur.execute("CREATE TABLE IF NOT EXISTS migration(name TEXT NOT NULL UNIQUE)")

    applied_migrations = set()
    for (migration_name,) in migrate_cur.execute("SELECT name FROM migration ORDER BY name"):
        applied_migrations.add(migration_name)

    for migration_name, migration_code in migrations:
        if migration_name in applied_migrations:
            continue  # Already applied: skip this one
        migrate_cur.executescript(migration_code)
        start_time = perf_counter()
        print(f"Applying migration {migration_name} to {db_file_name} database...")
        migrate_cur.execute("INSERT INTO migration VALUES(?)", (migration_name,))
        migrate_con.commit()
        print("Done in {:.6f} seconds".format(perf_counter() - start_time))
    migrate_con.close()


def migrate_account(account_id, migrations):
    account = Account.get_by_id(account_id)
    print(f"Migrating account {account.id} in {account.account_db_file_name} file...")

    migrate(account.account_db_file_name, migrations)


def run():
    # Auth database contains the list of all customer accounts' db files in the "account" table
    print("Running missing migrations on the auth database.")

    # Run auth module migrations first
    migrate(AuthModel.db_file_name, build_migrations_list("auth"))

    con = connect_to_db(AuthModel.db_file_name)
    with con:
        cur = con.execute("SELECT COUNT(*) FROM account")
    (account_count,) = cur.fetchone()
    print(f"Migrating {account_count} accounts.")

    migrations = build_migrations_list("accounts")

    account_ids = list(cur.execute("SELECT id FROM account ORDER BY id"))
    con.close()  # Close here to prevent locking the database file during account migrations

    for (account_id,) in account_ids:
        migrate_account(account_id, migrations=migrations)
    else:
        print("No account.")

    print("Done.")


if __name__ == "__main__":
    run()

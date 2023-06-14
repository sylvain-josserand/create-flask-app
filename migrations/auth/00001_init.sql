CREATE TABLE IF NOT EXISTS user
(
    "id"            INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name"          TEXT                              NOT NULL,                           -- name is 'Guest' for guest accounts (not signed up yet)
    "email"         TEXT                              NULL UNIQUE,                        -- email is null for guest accounts
    "password_hash" TEXT                              NULL,                               -- password is null for guest accounts
    "created"       TEXT                              NOT NULL default current_timestamp, -- It's a datetime
    "last_login"    TEXT                              NOT NULL default current_timestamp  -- It's a datetime
);

CREATE TABLE IF NOT EXISTS account
(
    id                   INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    account_db_file_name TEXT                              NOT NULL UNIQUE, -- Each account has its own database file
    name                 TEXT                              NOT NULL
);

CREATE TABLE IF NOT EXISTS user_account
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id    INTEGER                           NOT NULL,
    account_id INTEGER                           NOT NULL,
    role       TEXT                              NOT NULL CHECK (role IN ('admin', 'user', 'read-only')),
    UNIQUE (user_id, account_id),
    FOREIGN KEY (user_id) REFERENCES user (id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session
(
    id      INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    secret  TEXT                              NOT NULL UNIQUE,                    -- The secret is used to identify the session
    user_id INTEGER                           NOT NULL,
    created TEXT                              NOT NULL default current_timestamp, -- It's a datetime
    expires TEXT                              NOT NULL,                           -- It's a datetime. Don't delete, expire instead
    FOREIGN KEY (user_id) REFERENCES user (id) ON UPDATE CASCADE ON DELETE CASCADE
);

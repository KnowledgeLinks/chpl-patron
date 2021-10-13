ALTER TABLE {reg_table} RENAME TO old_{reg_table};

CREATE TABLE IF NOT EXISTS {reg_table} (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP, 
    date_retrieved DATETIME,
    patron_id VARCHAR NOT NULL UNIQUE,
    email VARCHAR NOT NULL,
    location VARCHAR NOT NULL DEFAULT 'unknown',
    boundary INTEGER NOT NULL DEFAULT -1
);

INSERT INTO {reg_table} SELECT * from old_{reg_table};

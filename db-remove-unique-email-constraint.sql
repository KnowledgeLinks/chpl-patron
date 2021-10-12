ALTER TABLE LibraryCardRequest RENAME TO old_LibraryCardRequest;

CREATE TABLE LibraryCardRequest (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP, 
    date_retrieved DATETIME,
    temp_number INTEGER,
    email VARCHAR NOT NULL
);

INSERT INTO LibraryCardRequest SELECT * from old_LibraryCardRequest;

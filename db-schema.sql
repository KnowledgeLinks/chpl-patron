-- CREATE TABLE Patron (
--     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--     first_name VARCHAR NOT NULL,
--     last_name VARCHAR NOT NULL,
--     birth_day VARCHAR NOT NULL
-- );

-- CREATE TABLE Location (
--     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--     address VARCHAR NOT NULL,
--     city VARCHAR NOT NULL,
--     state VARCHAR NOT NULL,
--     zip_code VARCHAR NOT NULL
-- );

-- CREATE TABLE Email (
--     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--     address VARCHAR NOT NULL
--     -- patron INTEGER,
--     -- FOREIGN KEY (patron) REFERENCES Patron (id)
-- );

-- CREATE TABLE Telephone (
--     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--     number VARCHAR NOT NULL,
--     patron INTEGER,
--     FOREIGN KEY (patron) REFERENCES Patron (id)
-- );

CREATE TABLE LibraryCardRequest (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP, 
    date_retrieved DATETIME,
    temp_number INTEGER,
    email VARCHAR NOT NULL
);


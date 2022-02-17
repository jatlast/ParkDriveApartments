-- 20220215 2:19 AM
-- Get the ALTER TABLE syntax correct before jumping straight to DROP/CREATE in case this is needed in the future.

-- Full path when created...
--  /home/PkDr/HA/code/DEV/sql/alter_ErrorLog.sql
-- To execute this file from the SQL command line...
--  source /home/PkDr/HA/code/DEV/sql/alter_ErrorLog.sql

-- Unnecessary TRANSACTION lines included as discovered for future reference
-- NOTE: lines need to end with semicolans ; except the SHOW for some reason
-- show create table ErrorLog\G
START TRANSACTION;

-- Show before...
SHOW CREATE TABLE PkDr.ErrorLog\G

-- Alter PkDr.ErrorLog table
ALTER TABLE IF EXISTS PkDr.ErrorLog;
MODIFY COLUMN IF EXISTS inserted datetime NOT NULL DEFAULT CURRENT_TIMESTAMP; -- worked within CLI
-- CHANGE inserted date datetime DEFAULT NULL;
-- CHANGE inserted date datetime DEFAULT CURRENT_TIMESTAMP AFTER author;
-- Disable NULL and add TIMESTAMP as default value
-- if it can be done at the same time
-- Show after
SHOW CREATE TABLE ErrorLog\G

COMMIT;

-- 3:31 AM - going to the SQL command line to test first since it gives error info while file execution does not

--ALTER TABLE IF EXISTS PkDr.ErrorLog MODIFY COLUMN IF EXISTS inserted datetime NOT NULL DEFAULT CURRENT_TIMESTAMP;
-- ERROR 1265 (01000): Data truncated for column 'inserted' at row 15
-- row 15 had a null value for inserted column
--  delete ErrorLog where uid = 15;
-- After deleting the row the above worked

-- FYI: I decided to keep the column name 'inserted' instead of chaning it to 'date'
-- Change column name from inserted to date
-- NOTE: RENAME is supposed to work with MariaDB 10.5.2 or newer
-- SELECT VERSION(); -- 10.5.12-MariaDB-0+deb11u1
--  Not available for my current version
-- RENAME COLUMN inserted TO date;

-- Consolidated version of what finally worked...
-- START TRANSACTION;
-- SHOW CREATE TABLE PkDr.ErrorLog\G
-- ALTER TABLE IF EXISTS PkDr.ErrorLog;
-- MODIFY COLUMN IF EXISTS inserted datetime NOT NULL DEFAULT CURRENT_TIMESTAMP; -- worked within CLI
-- SHOW CREATE TABLE ErrorLog\G
-- COMMIT;

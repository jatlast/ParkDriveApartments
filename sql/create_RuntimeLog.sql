-- 20220215 10:50 PM
-- Get the ALTER TABLE syntax correct before jumping straight to DROP/CREATE in case this is needed in the future.

-- FYI: MariaDB SQL statements can be ended with ;, \g, or \G

-- Full path when created...
--  /home/PkDr/HA/code/DEV/sql/create_ErrorLog.sql
-- To execute this file from the SQL command line...
--  source /home/PkDr/HA/code/DEV/sql/create_RuntimeLog.sql;

-- Drop / Create table...
-- I am going to take this opportunity to change the errtyp column name to errlevel

/* I left this line here to remind that it prevents the file from running via "source /path/sqlfile.sql;" */
-- START TRANSACTION;

-- Show before...
SHOW CREATE TABLE ErrorLog\G

-- Drop the old table...
DROP TABLE IF EXISTS ErrorLog\G

------------
-- uid --
------------
-- mediumint(8) unsigned (maximum length 16,777,215)
------------

------------
-- errtyp --
------------
--  column will contain the words (DEBUG, INFO, etc) but I am leaving the col size at 16 instead of 8
-- Based on python logging (https://docs.python.org/3/howto/logging.html)
--   0 - DEBUG   -   Detailed information, typically of interest only when diagnosing problems.
--   1 - INFO    -   Confirmation that things are working as expected.
--   2 - WARNING -   An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
--   3 - ERROR   -   Due to a more serious problem, the software has not been able to perform some function.
--   4 - CRITICAL-   A serious error, indicating that the program itself may be unable to continue running.

------------
-- msgtxt --
------------
-- TEXT (maximum length 65,535)
-- This column is made large to enable storing messages larger than the VARCHAR() max of 255 characters

-------------------- 
-- query_attempts --
-------------------- 
-- TINYINT (-127 - 127 signed | 255 unsigned?)
-------------------- 

CREATE OR REPLACE TABLE RuntimeLog (
  uid mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  inserted datetime NOT NULL DEFAULT current_timestamp(),
  author_date datetime DEFAULT NULL,
  author_name varchar(64) DEFAULT NULL,
  author_path varchar(128) DEFAULT NULL,
  author_options varchar(64) DEFAULT NULL,
  author_version varchar(16) DEFAULT NULL,
  author_address varchar(16) DEFAULT NULL,
  log_level TINYINT DEFAULT NULL,
  log_level_name varchar(8) DEFAULT NULL,
  log_message text DEFAULT NULL,
  exception_type varchar(64) DEFAULT NULL,
  exception_text varchar(255) DEFAULT NULL,
  query_text varchar(255) DEFAULT NULL,
  query_attempts TINYINT DEFAULT NULL,
  key0 varchar(64) DEFAULT NULL,
  val0 varchar(255) DEFAULT NULL,
  key1 varchar(64) DEFAULT NULL,
  val1 varchar(255) DEFAULT NULL,
  key2 varchar(64) DEFAULT NULL,
  val2 varchar(255) DEFAULT NULL,
  key3 varchar(64) DEFAULT NULL,
  val3 varchar(255) DEFAULT NULL,
  key4 varchar(64) DEFAULT NULL,
  val4 varchar(255) DEFAULT NULL,
  key5 varchar(64) DEFAULT NULL,
  val5 varchar(255) DEFAULT NULL,
  key6 varchar(64) DEFAULT NULL,
  val6 varchar(255) DEFAULT NULL,
  key7 varchar(64) DEFAULT NULL,
  val7 varchar(255) DEFAULT NULL,
  key8 varchar(64) DEFAULT NULL,
  val8 varchar(255) DEFAULT NULL,
  key9 varchar(64) DEFAULT NULL,
  val9 varchar(255) DEFAULT NULL,
  PRIMARY KEY (uid)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4\G

SHOW CREATE TABLE RuntimeLog\G

SHOW CREATE TABLE ErrorLog\G

/*
CREATE OR REPLACE TABLE ErrorLog (
  uid mediumint(9) NOT NULL AUTO_INCREMENT,
  inserted datetime NOT NULL DEFAULT current_timestamp(),
  author varchar(64) DEFAULT NULL,
  executed datetime DEFAULT NULL,
  errtyp varchar(16) DEFAULT NULL,
  exceptxt varchar(255) DEFAULT NULL,
  querytxt varchar(255) DEFAULT NULL,
  msgtxt text DEFAULT NULL,
  key0 varchar(64) DEFAULT NULL,
  val0 varchar(255) DEFAULT NULL,
  key1 varchar(64) DEFAULT NULL,
  val1 varchar(255) DEFAULT NULL,
  key2 varchar(64) DEFAULT NULL,
  val2 varchar(255) DEFAULT NULL,
  key3 varchar(64) DEFAULT NULL,
  val3 varchar(255) DEFAULT NULL,
  key4 varchar(64) DEFAULT NULL,
  val4 varchar(255) DEFAULT NULL,
  key5 varchar(64) DEFAULT NULL,
  val5 varchar(255) DEFAULT NULL,
  key6 varchar(64) DEFAULT NULL,
  val6 varchar(255) DEFAULT NULL,
  key7 varchar(64) DEFAULT NULL,
  val7 varchar(255) DEFAULT NULL,
  key8 varchar(64) DEFAULT NULL,
  val8 varchar(255) DEFAULT NULL,
  key9 varchar(64) DEFAULT NULL,
  val9 varchar(255) DEFAULT NULL,
  PRIMARY KEY (uid)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

*/
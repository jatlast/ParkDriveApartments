/*
temperature_expiration_minutes: 30
temperature_value_if_expired_celsius: 22.22 # (72 F − 32) × 5/9 = 22.222 C
temperature_value_minimum_celsius: 10 # (50 F − 32) × 5/9 = 10 C 
temperature_value_maximum_celsius: 37.778 # (100 F − 32) × 5/9 = 37.778 C

source /home/PkDr/HA/code/DEV/sql/sp_get_kiosk_temp_fahrenheit.sql;

SHOW PROCEDURE CODE sp_get_kiosk_temp_fahrenheit;
*/

DELIMITER //

CREATE PROCEDURE
  sp_get_kiosk_temp_fahrenheit
  (
      apt_or_bld_num TINYINT
  )
  READS SQL DATA              /* Data access clause */
  BEGIN                       /* Routine body */
    DECLARE number_of_rows_to_subtract INT;
    DECLARE temperature_expiration_minutes TINYINT;
    DECLARE temperature_value_if_expired_celsius FLOAT;
    DECLARE temperature_value_minimum_celsius FLOAT;
    DECLARE temperature_value_maximum_celsius FLOAT;

    SET number_of_rows_to_subtract = 200;
    SET temperature_expiration_minutes = 30;
    SET temperature_value_if_expired_celsius = 22.22; /* (72 F − 32) × 5/9 = 22.222 C */
    SET temperature_value_minimum_celsius = 10;       /* (50 F − 32) × 5/9 = 10 C  */
    SET temperature_value_maximum_celsius = 37.778;   /* (100 F − 32) × 5/9 = 37.778 C C */
    
    SELECT (IF(TIMESTAMPDIFF(MINUTE,taken,NOW()) < temperature_expiration_minutes, temperature, 72)* 9/5)+ 32 AS temperature
    FROM Thermostats
        WHERE uid > (SELECT MAX(uid)-number_of_rows_to_subtract FROM Thermostats)
            AND temperature BETWEEN temperature_value_minimum_celsius 
                                AND temperature_value_maximum_celsius
            AND apt = apt_or_bld_num
        ORDER BY uid DESC
        LIMIT 1;
  END;
//

DELIMITER ;

CALL sp_get_kiosk_temp_fahrenheit(12);

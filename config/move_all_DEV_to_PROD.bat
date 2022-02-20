:: Move all PkDr scripts from DEV directory to the PROD (live) directory
:: robocopy 
::      https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
:: Paths
::  JTB 2020 Laptop
::      Z:\PkDr\HA\code\DEV\config\move_all_DEV_to_PROD.bat
::  Network Share IP
::      \\10.16.0.22\PkDr\HA\code\DEV\config\move_all_DEV_to_PROD.bat
:: Files effected:
:: DEV/

@echo off

@REM  config/
@REM      pkdr_config.yaml
robocopy "Z:\PkDr\HA\code\DEV\config" "Z:\PkDr\HA\code\PROD\config" "pkdr_config.yaml" /z

@REM  python/
@REM      pkdr_i2c_to_db.py
robocopy "Z:\PkDr\HA\code\DEV\python" "Z:\PkDr\HA\code\PROD\python" "pkdr_i2c_to_db.py" /z
@REM      pkdr_kiosk_doorbell.py
robocopy "Z:\PkDr\HA\code\DEV\python" "Z:\PkDr\HA\code\PROD\python" "pkdr_kiosk_doorbell.py" /z
@REM      pkdr_utils.py
robocopy "Z:\PkDr\HA\code\DEV\python" "Z:\PkDr\HA\code\PROD\python" "pkdr_utils.py" /z

exit /b


:: set X=<days>

:: set pkdr_utils_needed_by_python_scripts=yaml_test.py

:: set from_DEV_python_dir=Z:\PkDr\HA\code\DEV\python
:: set to_PROD_python_dir=Z:\PkDr\HA\code\PROD\python

:: robocopy from_DEV_python_dir to_PROD_python_dir pkdr_utils_needed_by_python_scripts /z


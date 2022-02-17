#!/usr/bin/python

# ------------
# JTB 20220213
# ------------
# This code is (or will be) required by ...
#   PkDr Kiosks: Apt 01 - 16 & B1 - B4
# The Reason for Existence
#   - This script polls ic2 for a locally connected HTU21D or SHT31D sensor
#   -   temperature & humidity readings are inserted into a remote MariaDB database for use by Home Assistant
# The code ...
#   - is a consolidation of two previous scripts (pkdr_htu21d_db_v3 & pkdr_sht31d_db_v3)
#   - depends on config/secrets.yaml
#   - depends on pkdr_utils.py
#   - runs in-place on the NAS drive
#   - is executed every five minutes by 'sudo crontab -e' cron job
# The Service ...
#   - configuration location
#       /etc/systemd/system/pkdr_kiosk_doorbell.service
#   - can be managed using systemctl to (stop, start, restart, enable, disable, etc)
# ------------

# Install the required package...
#   sudo pip3 install adafruit-circuitpython-htu21d
#       https://learn.adafruit.com/adafruit-htu21d-f-temperature-humidity-sensor/python-circuitpython
#   sudo pip3 install adafruit-circuitpython-sht31d
#       https://learn.adafruit.com/adafruit-sht31-d-temperature-and-humidity-sensor-breakout/python-circuitpython

import socket
import datetime
# from mysql.connector import errorcode
# from mysql.connector import Error
# import mysql.connector
import time
import board
import busio
import adafruit_htu21d  # htu21d - Temperature & Humidity
import adafruit_sht31d  # sht31d - Temperature & Humidity
import argparse
import pkdr_utils

# allow command line options
parser = argparse.ArgumentParser(description="Reads the I2C connected sensor (HTU21D or SHT31D) and log the temperature & humidity to the mySQL DB PkDr.Thermostats table")
parser.add_argument(
    "-v",
    "--verbosity",
    type=int,
    choices=[0, 1, 2, 3],
    default=0,
    help="increase output verbosity",
)
args = parser.parse_args()

# variables that are useful to pass around
variables_dict = {
    "program_name": parser.prog,
    "verbosity": args.verbosity,
    "sensor_detected": "",
    "htu21d_exception_flag": False,
    "htu21d_exception_msg": "",
    "sht31d_exception_flag": False,
    "sht31d_exception_msg": "",
}

if not pkdr_utils.initialize_config_dict(variables_dict):
    print("{}: Configuration Failure {}".format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['error_msg']))
else:
    # Create library object using our Bus I2C port
    i2c = busio.I2C(board.SCL, board.SDA)
    temperature = 0
    humidity = 0

    # https://docs.python.org/3/tutorial/errors.html
    # ----- Try Accessing HTU21D -----
    try:
        sensor = adafruit_htu21d.HTU21D(i2c)
        variables_dict["sensor_detected"] = "HTU21D"
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
    except ValueError as err:
        variables_dict["htu21d_exception_msg"] = "ValueError ({})".format(err)
        variables_dict["htu21d_exception_flag"] = True
    except Exception as err:
        variables_dict["htu21d_exception_msg"] = "Unexptected ({})|({}) - This should never happen".format(type(err), err)
        pkdr_utils.config_dict['db_table_dict']['msgtxt'] = "CODE: {} requires updating".format(pkdr_utils.config_dict['program_path'])
        variables_dict["htu21d_exception_flag"] = True

    if temperature == 0:
        # ----- Try Accessing SHT31D -----
        try:
            sensor = adafruit_sht31d.SHT31D(i2c)
            variables_dict["sensor_detected"] = "SHT31D"
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
        except ValueError as err:
            variables_dict["sht31d_exception_msg"] = "ValueError ({})".format(err)
            variables_dict["sht31d_exception_flag"] = True
        except Exception as err:
            variables_dict["sht31d_exception_msg"] = "Unexptected ({})|({}) - This should never happen".format(type(err), err)
            pkdr_utils.config_dict['db_table_dict']['msgtxt'] = "CODE: {} requires updating".format(pkdr_utils.config_dict['program_path'])
            variables_dict["sht31d_exception_flag"] = True

    # ----- Log Any Coniguration Errors to DB -----
    if (variables_dict["htu21d_exception_flag"]
        or variables_dict["sht31d_exception_flag"]
        ):
            # ----- Did both sensors fail? -----
            if (variables_dict["htu21d_exception_flag"] and variables_dict["sht31d_exception_flag"]):
                pkdr_utils.config_dict['db_table_dict']['errtyp'] = pkdr_utils.config_dict['lookup_error_num_to_name_dict'][4] # 4 = CRITICAL
                pkdr_utils.config_dict['db_table_dict']['exceptxt'] = variables_dict["htu21d_exception_msg"] + ' & ' + variables_dict["sht31d_exception_msg"]
                pkdr_utils.config_dict['db_table_dict']['key5'] = 'HTU21D'
                pkdr_utils.config_dict['db_table_dict']['val5'] = 'Detection Failure'
                pkdr_utils.config_dict['db_table_dict']['key6'] = 'SHT31D'
                pkdr_utils.config_dict['db_table_dict']['val6'] = 'Detection Failure'
            # ----- Did either sensor fail? -----
            elif (variables_dict["htu21d_exception_flag"] or variables_dict["sht31d_exception_flag"]):
                pkdr_utils.config_dict['db_table_dict']['errtyp'] = pkdr_utils.config_dict['lookup_error_num_to_name_dict'][2] # 2 = WARNING

                if variables_dict["htu21d_exception_flag"]:
                    pkdr_utils.config_dict['db_table_dict']['exceptxt'] = variables_dict["htu21d_exception_msg"]
                    pkdr_utils.config_dict['db_table_dict']['key5'] = 'HTU21D'
                    pkdr_utils.config_dict['db_table_dict']['val5'] = 'Detection Failure'
                elif variables_dict["sht31d_exception_flag"]:
                    pkdr_utils.config_dict['db_table_dict']['exceptxt'] = variables_dict["sht31d_exception_msg"]
                    pkdr_utils.config_dict['db_table_dict']['key5'] = 'SHT31D'
                    pkdr_utils.config_dict['db_table_dict']['val5'] = 'Detection Failure'

            # call utility function to insert into the DB
            pkdr_utils.db_generic_insert('ErrorLog')

    if temperature != 0:
        temperature = sensor.temperature
        humidity = sensor.relative_humidity

        if variables_dict["verbosity"] > 1:
            print("Using sensor type ({})".format(variables_dict["sensor_detected"]),)
            print("Befor DB call: {} F | {} %".format(round(((temperature * 9 / 5) + 32), 2),round(humidity, 2),))

        # Initialize DB Insert variables...
        pkdr_utils.config_dict['db_insert_dict']['apt'] = pkdr_utils.config_dict['num_int']
        pkdr_utils.config_dict['db_insert_dict']['temperature'] = temperature
        pkdr_utils.config_dict['db_insert_dict']['humidity'] = humidity
        pkdr_utils.config_dict['db_insert_dict']['taken'] = str(datetime.datetime.now())

        # call utility function to insert into the DB
        pkdr_utils.db_generic_insert('Thermostats')

    # SQL for checking Thermostats table...
    # MariaDB [PkDr]> select apt, temperature as C, (temperature * 9/5) + 32 as F, taken from Thermostats order by uid desc limit 20;



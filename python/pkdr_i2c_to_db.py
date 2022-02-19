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
# WARNING: old boxes still use the old version on the old NAS...
#   Pi = /usr/bin/python /home/PkDr/HA/code/python/pkdr_htu21df_db.py >> /home/pi/logs/htu2ldf.log 2>&1
#  Old = \\10.16.0.21\HA\code\python\pkdr_htu21df_db.py
# Still deciding on dir format...
#  New = \\10.16.0.22\HA\code\python\pkdr_htu21df_db.py
# ------------

# Install the required package...
#   sudo pip3 install adafruit-circuitpython-htu21d
#       https://learn.adafruit.com/adafruit-htu21d-f-temperature-humidity-sensor/python-circuitpython
#   sudo pip3 install adafruit-circuitpython-sht31d
#       https://learn.adafruit.com/adafruit-sht31-d-temperature-and-humidity-sensor-breakout/python-circuitpython

from cgitb import reset
from cmath import log
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
from adafruit_bus_device.i2c_device import I2CDevice # for specifying specific address for i2c device initialization
import argparse
import pkdr_utils

# allow command line options
parser = argparse.ArgumentParser(description="Reads the I2C connected sensor (HTU21D or SHT31D) and logs the temperature & humidity to the mySQL DB PkDr.Thermostats table")
parser.add_argument(
    '-v',
    '--verbosity',
    type=int,
    choices=[0, 1, 2, 3, 4],
    default=0,
    help='increase output verbosity',
)
parser.add_argument(
    '-st',
    '--sensor_type',
    type=str,
    choices=['HTU21D', 'SHT31D'],
    default='HTU21D',
    help='I2C sensor name: HTU21D or SHT31D',
)
parser.add_argument(
    '-sta',
    '--sensor_type_address',
    type=lambda x: int(x,16), # on the fly hex type
    choices=[0x40, 0x44],
    default=0x40,
    help="I2C sensor address: for sensor type HTU21D use 0x40 or 64, for sensor type SHT31D use 0x44 or 68. FYI: CLI: 'i2cdetect -y 1' checks if any sensors are connected",
)
args = parser.parse_args()

# variables that are useful to pass around
variables_dict = {
    'program_name': parser.prog,
    'program_description': parser.description,
    'program_usage': parser.format_usage(),
    'program_help': parser.format_help(),
    'verbosity': args.verbosity,
    'sensor_type': args.sensor_type,
    'sensor_type_address': args.sensor_type_address,
}

if not pkdr_utils.initialize_config_dict(variables_dict):
    print('{}: Configuration Failure {}'.format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['error_msg']))
else:
    # Create library object using Adafruit's Bus I2C port
    i2c = busio.I2C(board.SCL, board.SDA) # (SCL, SDA) default | returns <busio.I2C object at 0x763d6e50>
    temperature = 0
    humidity = 0
    log_text = ''

    # Default sensor to arg defaults...
    sensor_type = variables_dict['sensor_type']
    # set the appropriate address regardless of the cli options
    if sensor_type == 'HTU21D':
        sensor_address = 0x40
    elif sensor_type == 'SHT31D':
        sensor_address = 0x44
    # use the cli option if the sensor type is not recognized
    else:
        sensor_address = variables_dict['sensor_type_address']
    
    sensor_error_flag = False

    # Get sensor settings from config file parameters...
    if not pkdr_utils.config_dict['sensor_type_error_flag']:
        if not pkdr_utils.config_dict['sensor_type_error_flag']:
            if pkdr_utils.config_dict['sensor_type'] == 'HTU21D':
                sensor_type = pkdr_utils.config_dict['sensor_type']
                sensor_address = pkdr_utils.config_dict['sensor_type_address']
            elif pkdr_utils.config_dict['sensor_type'] == 'SHT31D':
                sensor_type = pkdr_utils.config_dict['sensor_type']
                sensor_address = pkdr_utils.config_dict['sensor_type_address']
            else:
                sensor_error_flag = True
                sensor_error_msg = 'Config Error: sensor_type ({}) not recognized'.format(pkdr_utils.config_dict['sensor_type'])

    # Try instantiating an i2c object using a the spcific address determined above...
    exception_msg = ''
    exception_type = ''
    exception_flag = False
    try:
        # the exception handling is now done with a specific address
        sensor = I2CDevice(i2c, sensor_address) # returns object <adafruit_bus_device.i2c_device.I2CDevice object at 0x760d8f40>
    except ValueError as err:
        exception_type = '{}'.format(type(err))
        exception_msg = '({}) I2CDevice({}, {}) raised: ValueError {}'.format(sensor_type, str(i2c), sensor_address, err)
        exception_flag = True
    except Exception as err:
        exception_type = '{}'.format(type(err))
        exception_msg = '({}) I2CDevice({}, {}) raised: Unexptected ({})|({}) - This should never happen'.format(sensor_type, str(i2c), sensor_address, type(err), err)
        pkdr_utils.config_dict['db_table_dict']['log_message'] = 'CODE: {} requires updating'.format(pkdr_utils.config_dict['program_path'])
        exception_flag = True

    # ----- Log Any Coniguration Errors to DB -----
    if exception_flag or sensor_error_flag:
        log_level = 4 # 4 = CRITICAL
        pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
        pkdr_utils.config_dict['db_table_dict']['key5'] = 'sensor_type'
        pkdr_utils.config_dict['db_table_dict']['val5'] = sensor_type
        pkdr_utils.config_dict['db_table_dict']['key6'] = 'sensor_address'
        pkdr_utils.config_dict['db_table_dict']['val6'] = sensor_address
        if exception_flag:
            pkdr_utils.config_dict['db_table_dict']['exception_type'] = exception_type
            pkdr_utils.config_dict['db_table_dict']['exception_text'] = exception_msg
        elif sensor_error_flag:
            pkdr_utils.config_dict['db_table_dict']['log_message'] = sensor_error_msg
        pkdr_utils.db_generic_insert()
    else:
        if sensor_type == 'HTU21D' and sensor_address == 0x40:
            sensor = adafruit_htu21d.HTU21D(i2c)
        elif sensor_type == 'SHT31D' and sensor_address == 0x44:
            sensor = adafruit_sht31d.SHT31D(i2c)
        else:
            sensor_error_flag = True
            sensor_error_msg = 'Config Error: sensor_type({}) has incorrect address({}) aka({})'.format(sensor_type, sensor_address, hex(sensor_address))
            pkdr_utils.config_dict['db_table_dict']['log_message'] = sensor_error_msg
            pkdr_utils.db_generic_insert()

        if not sensor_error_flag:
            temperature = sensor.temperature
            humidity = sensor.relative_humidity

            log_text += 'Using sensor sensor_type({}) @ int({}) hex({})'.format(sensor_type, sensor_address, hex(sensor_address))
            log_text += '\n'
            log_text += 'Befor DB call: {} F | {} %'.format(round(((temperature * 9 / 5) + 32), 2),round(humidity, 2),)

            if variables_dict['verbosity'] > 1:
                print(log_text)

            # Initialize DB Insert variables...
            pkdr_utils.config_dict['db_insert_dict']['apt'] = pkdr_utils.config_dict['num_int']
            pkdr_utils.config_dict['db_insert_dict']['temperature'] = temperature
            pkdr_utils.config_dict['db_insert_dict']['humidity'] = humidity
            pkdr_utils.config_dict['db_insert_dict']['taken'] = str(datetime.datetime.now())

            # call utility function to insert into the DB
            pkdr_utils.db_generic_insert('Thermostats')

    # SQL for checking Thermostats table...
    # MariaDB [PkDr]> select apt, temperature as C, (temperature * 9/5) + 32 as F, taken from Thermostats order by uid desc limit 20;

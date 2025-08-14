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
# To-Do:
#   20220222 - Considering the propensity of sensors to hang, this scrip should probably be updated to be a
#     scheduler to replace crontab mindlessly spanning new instances when previous instances have yet to return.
#     Such an update to this program would make it multi-threaded -- spanning a thread anytime it attempts to 
#     interact with the sensor.  Then it would kill any thread that did not return in a timely fashion.
# ------------

# Install the required package...
#   sudo pip3 install adafruit-circuitpython-htu21d
#       https://learn.adafruit.com/adafruit-htu21d-f-temperature-humidity-sensor/python-circuitpython
#   sudo pip3 install adafruit-circuitpython-sht31d
#       https://learn.adafruit.com/adafruit-sht31-d-temperature-and-humidity-sensor-breakout/python-circuitpython
#   sudo pip3 install adafruit-circuitpython-sht4x
#       https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor/python-circuitpython

# from cgitb import reset
# from cmath import log
# import socket
import datetime
# from mysql.connector import errorcode
# from mysql.connector import Error
# import mysql.connector
import time # needed for measuring code block execution duration to monitor sensor interaction times
import board
import busio
import adafruit_htu21d  # htu21d - Temperature & Humidity
import adafruit_sht31d  # sht31d - Temperature & Humidity
import adafruit_sht4x   # sht4x  - Temperature & Humidity
from adafruit_bus_device.i2c_device import I2CDevice # for specifying specific address for i2c device initialization
import argparse
import random
# import pkdr_utils
from pkdr_utils import utils as pkdr_utils

max_duration_program = 2.0
max_duration_block = 0.5
program_start_time = time.time()

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
    choices=['HTU21D', 'SHT31D', 'SHT4xD'],
    default='HTU21D',
    help='I2C sensor name: HTU21D, SHT31D, or SHT4xD'
)
parser.add_argument(
    '-sta',
    '--sensor_type_address',
    type=lambda x: int(x,16), # on the fly hex type
    choices=[0x40, 0x44],
    default=0x40,
    help="I2C sensor address: for sensor type HTU21D use 0x40 or 64, for sensor type SHT31D-SHT4xD use 0x44 or 68. FYI: CLI: 'i2cdetect -y 1' checks if any sensors are connected",
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
    # ----------------
    # RuntimeLog (key#/val#) Variables Convention
    # ----------------
    # set in pkdr_utils.py
    # ----------------
    # key0 - key_log
    # key1 - apt_or_bld
    # ----------------
    # set in this program...
    # ----------------
    # key2 - sensor_type
    # key3 - sensor_address
    # key4 - temperature
    # key5 - humidity
    # key6 - duration->sensor_set_generic
    # key7 - duration->sensor_set_specific
    # key8 - duration->sensor_read_temperature
    # key9 - duration->program_execution
    # duration->sensor_read_humidity # not currently used
    # ----------------

    # initialized at top for reference & restating key# w/ val# for readability within the body of the program...
    pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
    pkdr_utils.config_dict['db_table_dict']['val0'] = 'sensor->' # set root of log_key value to be appended to based on program flow
    # pkdr_utils.config_dict['db_table_dict']['key1'] = 'apt_or_bld'
    # pkdr_utils.config_dict['db_table_dict']['key2'] = 'sensor_type'
    # pkdr_utils.config_dict['db_table_dict']['key3'] = 'sensor_address'
    # pkdr_utils.config_dict['db_table_dict']['key4'] = 'temperature'
    # pkdr_utils.config_dict['db_table_dict']['key5'] = 'humidity'
    # pkdr_utils.config_dict['db_table_dict']['key6'] = 'duration->sensor_set_generic'
    # pkdr_utils.config_dict['db_table_dict']['key7'] = 'duration->sensor_set_specific'
    # pkdr_utils.config_dict['db_table_dict']['key8'] = 'duration->sensor_read_temperature'
    # pkdr_utils.config_dict['db_table_dict']['key9'] = 'duration->program_execution'    

    # Create library object using Adafruit's Bus I2C port
    i2c = busio.I2C(board.SCL, board.SDA) # (SCL, SDA) default | returns <busio.I2C object at 0x763d6e50>
    temperature = 0.0
    humidity = 0.0
    log_text = ''
    code_block_times_dict = {
        # initialize to negative since durations are always positive...
        'program_execution' : -1.0,
        'sensor_set_generic' : -1.0,
        'sensor_set_specific' : -1.0,
        'sensor_read_temperature' : -1.0,
        'sensor_read_humidity' : -1.0,
        'db_insert_readings' : -1.0,
    }

    # Default sensor to arg defaults...
    sensor_type = variables_dict['sensor_type']
    # set the appropriate address regardless of the cli options
    if sensor_type == 'HTU21D':
        sensor_address = 0x40
    elif sensor_type == 'SHT31D':
        sensor_address = 0x44
    elif sensor_type == 'SHT4xD':
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
            elif pkdr_utils.config_dict['sensor_type'] == 'SHT4xD':
                sensor_type = pkdr_utils.config_dict['sensor_type']
                sensor_address = pkdr_utils.config_dict['sensor_type_address']
            else:
                sensor_error_flag = True
                sensor_error_msg = 'Config Error: sensor_type ({}) not recognized'.format(pkdr_utils.config_dict['sensor_type'])

    # These can be set here and shared because they are not updated....
    # pkdr_utils.config_dict['db_table_dict']['key2'] = 'sensor_type'
    # pkdr_utils.config_dict['db_table_dict']['val2'] = sensor_type
    # pkdr_utils.config_dict['db_table_dict']['key3'] = 'sensor_address'
    # pkdr_utils.config_dict['db_table_dict']['val3'] = hex(sensor_address)
    pkdr_utils.db_variables_add_key_value('sensor_type', sensor_type)
    pkdr_utils.db_variables_add_key_value('sensor_address', hex(sensor_address))
    
    block_start_time = time.time()

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
    except BaseException as err:
        exception_type = '{}'.format(type(err))
        exception_msg = '({}) I2CDevice({}, {}) raised: Unexpected ({})|({})'.format(sensor_type, str(i2c), sensor_address, type(err), err)
        exception_flag = True

    block_end_time = time.time()
    code_block_times_dict['sensor_set_generic'] = round((block_end_time - block_start_time), 6)
    # pkdr_utils.config_dict['db_table_dict']['key6'] = 'duration->sensor_set_generic'
    # pkdr_utils.config_dict['db_table_dict']['val6'] = code_block_times_dict['sensor_set_generic']

    if variables_dict['verbosity'] > 3:
        pkdr_utils.eprint('{} for exception checking: sensor = generic'.format(code_block_times_dict['sensor_set_generic']))

    # ----- Log Any Coniguration Errors to DB -----
    if (exception_flag or sensor_error_flag or pkdr_utils.config_dict['sensor_temperature_window_error_flag']):
        log_level = 4 # 4 = CRITICAL
        pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level]
        if exception_flag:
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'exception->set_generic'
            pkdr_utils.config_dict['db_table_dict']['exception_type'] = exception_type
            pkdr_utils.config_dict['db_table_dict']['exception_text'] = exception_msg
        elif sensor_error_flag:
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'config->error'
            pkdr_utils.config_dict['db_table_dict']['log_message'] = sensor_error_msg
        elif pkdr_utils.config_dict['sensor_temperature_window_error_flag']:
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'config->temperature_window->error'
            pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Config Error: Sensor Window not configured for valid temperature readings in PkDr config YAML.'
        else:
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'type_or_address'

        pkdr_utils.db_variables_add_dict(code_block_times_dict)
        pkdr_utils.db_generic_insert()
    else:
        if not sensor_error_flag:
            block_start_time = time.time()

            # Try accessing the sensor for a temperature reading...
            exception_msg = ''
            exception_type = ''
            exception_flag = False
            no_sensor_tried_flag = True
            read_attempt_string_for_info = 'sensor = adafruit_'
            try:
                if sensor_type == 'HTU21D' and sensor_address == 0x40:
                    read_attempt_string_for_info += 'htu21d.HTU21D(i2c)'
                    no_sensor_tried_flag = False
                    sensor = adafruit_htu21d.HTU21D(i2c) # 20220222 7:45 AM - this sensor is causing the program to hang
                elif sensor_type == 'SHT31D' and sensor_address == 0x44:
                    read_attempt_string_for_info += 'sht31d.SHT31D(i2c)'
                    no_sensor_tried_flag = False
                    sensor = adafruit_sht31d.SHT31D(i2c)
                elif sensor_type == 'SHT4xD' and sensor_address == 0x44:
                    read_attempt_string_for_info += 'sht4x.SHT4x(i2c)'
                    no_sensor_tried_flag = False
                    sensor = adafruit_sht4x.SHT4x(i2c)

                    # if statement for a 50/50 chance...
                    # if random.randint(0, 1) == 0:
                    # if statement for a 90/10 chance of setting the mode to NOHEAT_HIGHPRECISION or LOWHEAT_100MS
                    if random.random() < 0.9:
                        sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
                    else:
                        sensor.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
                    
                    read_attempt_string_for_info += ' #:({})'.format(sensor.serial_number)
                    read_attempt_string_for_info += ' mode:({})'.format(adafruit_sht4x.Mode.string[sensor.mode])
            # OSError: [Errno 121] Remote I/O error
            except OSError as err:
                exception_type = '{}'.format(type(err))
                exception_msg = '({} @ {}) {} raised: OSError ({})|({})'.format(sensor_type, sensor_address, read_attempt_string_for_info, type(err), err)
                exception_flag = True
            except BaseException as err:
                exception_type = '{}'.format(type(err))
                exception_msg = '({} @ {}) {} raised: Unexpected ({})|({})'.format(sensor_type, sensor_address, read_attempt_string_for_info, type(err), err)
                exception_flag = True

            block_end_time = time.time()
            code_block_times_dict['sensor_set_specific'] = round((block_end_time - block_start_time), 6)
            # pkdr_utils.config_dict['db_table_dict']['key7'] = 'duration->sensor_set_specific'
            # pkdr_utils.config_dict['db_table_dict']['val7'] = code_block_times_dict['sensor_set_specific']
            if variables_dict['verbosity'] > 3:
                pkdr_utils.eprint('{} for {} @ {} {}'.format(code_block_times_dict['sensor_set_specific'], sensor_type, hex(sensor_address), read_attempt_string_for_info))

            # ----- Log Any Coniguration Errors to DB -----
            if exception_flag:
                log_level = 4 # 4 = CRITICAL
                pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
                pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level]
                pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Sensor Exception: {}'.format(read_attempt_string_for_info)
                pkdr_utils.config_dict['db_table_dict']['exception_type'] = exception_type
                pkdr_utils.config_dict['db_table_dict']['exception_text'] = exception_msg
                pkdr_utils.config_dict['db_table_dict']['val0'] += 'exception->set_specific'
                pkdr_utils.db_variables_add_dict(code_block_times_dict)
                pkdr_utils.db_generic_insert()
            elif no_sensor_tried_flag:
                sensor_error_flag = True
                log_level = 4 # 4 = CRITICAL
                pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
                pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level]
                pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Config Error: sensor_type({}) has incorrect address({}) aka({})'.format(sensor_type, sensor_address, hex(sensor_address))
                pkdr_utils.config_dict['db_table_dict']['val0'] += 'config->type_address->error'
                pkdr_utils.db_variables_add_dict(code_block_times_dict)
                pkdr_utils.db_generic_insert()
            else:
                block_start_time = time.time()

                # Try accessing the sensor for a temperature reading...
                temperature = 0.0
                humidity = 0.0
                exception_msg = ''
                exception_type = ''
                exception_flag = False
                try:
                    if sensor_type == 'HTU21D':
                        temperature = sensor.temperature
                    elif sensor_type == 'SHT31D':
                        temperature = sensor.temperature
                        # only set the heater 10% of the time...
                        if random.random() < 0.1:
                            sensor.heater = True
                            # print("Sensor Heater status =", sensor.heater)
                            log_text += "Sensor Heater status = {}".format(sensor.heater)
                            time.sleep(1)
                            sensor.heater = False
                            # print("Sensor Heater status =", sensor.heater)                    
                            log_text += " before sleep(1) {} after.".format(sensor.heater)
                    elif sensor_type == 'SHT4xD':
                        # print("Found SHT4x with serial number", hex(sensor.serial_number))
                        # sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
                        # Can also set the mode to enable heater
                        # sensor.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
                        # print("Current mode is: ", adafruit_sht4x.Mode.string[sensor.mode])
                        temperature, humidity = sensor.measurements
                # OSError: [Errno 121] Remote I/O error
                except OSError as err:
                    exception_type = '{}'.format(type(err))
                    exception_msg = '({} @ {}) sensor.temperature raised: OSError ({})|({})'.format(sensor_type, sensor_address, type(err), err)
                    exception_flag = True
                except BaseException as err:
                    exception_type = '{}'.format(type(err))
                    exception_msg = '({} @ {}) sensor.temperature raised: Unexpected ({})|({})'.format(sensor_type, sensor_address, type(err), err)
                    exception_flag = True

                # pkdr_utils.config_dict['db_table_dict']['key4'] = 'temperature'
                # pkdr_utils.config_dict['db_table_dict']['val4'] = temperature
                pkdr_utils.db_variables_add_key_value('temperature', temperature)

                block_end_time = time.time()
                code_block_times_dict['sensor_read_temperature'] = round((block_end_time - block_start_time), 6)
                # pkdr_utils.config_dict['db_table_dict']['key8'] = 'duration->sensor_read_temperature'
                # pkdr_utils.config_dict['db_table_dict']['val8'] = code_block_times_dict['sensor_read_temperature']
                if variables_dict['verbosity'] > 3:
                    pkdr_utils.eprint('{} for sensor {} @ {} to execute sensor.temperature'.format(code_block_times_dict['sensor_read_temperature'], sensor_type, hex(sensor_address)))

                # ----- Log Any Coniguration Errors to DB -----
                if exception_flag:
                    log_level = 4 # 4 = CRITICAL
                    pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
                    pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level]
                    pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Sensor Exception: temperature = sensor.temperature'
                    pkdr_utils.config_dict['db_table_dict']['exception_type'] = exception_type
                    pkdr_utils.config_dict['db_table_dict']['exception_text'] = exception_msg
                    pkdr_utils.config_dict['db_table_dict']['val0'] += 'exception->temperature'
                    pkdr_utils.db_variables_add_dict(code_block_times_dict)
                    pkdr_utils.db_generic_insert()
                else:
                    block_start_time = time.time()

                    if sensor_type == 'HTU21D':
                        humidity = sensor.relative_humidity
                    elif sensor_type == 'SHT31D':
                        humidity = sensor.relative_humidity
                    elif sensor_type == 'SHT4xD':
                        if humidity == 0.0:
                            temperature, humidity = sensor.measurements

                    # pkdr_utils.config_dict['db_table_dict']['key5'] = 'humidity'
                    # pkdr_utils.config_dict['db_table_dict']['val5'] = humidity
                    pkdr_utils.db_variables_add_key_value('humidity', humidity)

                    block_end_time = time.time()
                    code_block_times_dict['sensor_read_humidity'] = round((block_end_time - block_start_time), 6)
                    # set dict but may be overwritten later
                    # pkdr_utils.config_dict['db_table_dict']['key?'] = 'duration->sensor_read_humidity'
                    # pkdr_utils.config_dict['db_table_dict']['val?'] = code_block_times_dict['sensor_read_humidity']
                    if variables_dict['verbosity'] > 3:
                        pkdr_utils.eprint('{} for sensor {} @ {} to execute sensor.relative_humidity'.format(code_block_times_dict['sensor_read_humidity'], sensor_type, hex(sensor_address)))

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

                    block_start_time = time.time()

                    pkdr_utils.db_generic_insert('Thermostats')

                    block_end_time = time.time()
                    code_block_times_dict['db_insert_readings'] = round((block_end_time - block_start_time), 6)
                    if variables_dict['verbosity'] > 3:
                        pkdr_utils.eprint('{} for db insert thermostats'.format(code_block_times_dict['db_insert_readings']))
                    
                    # temperature = -1 # used to trigger database insert after the temperature has been inserted into the Thermostats table.
                    # 20220221 - Apt12's faulty HTU21D is reading negative temperatures, so I am updating the logic to check for such signs of a faulty sensor.
                    # Also, since HA uses these values to determin if it should turn on the heat, the script should not log any temperature outside of a certain window.
                    if (temperature > pkdr_utils.config_dict['temperature_valid_max'] or temperature < pkdr_utils.config_dict['temperature_valid_min'] or code_block_times_dict['program_execution'] > max_duration_program):
                        program_end_time = time.time()
                        code_block_times_dict['program_execution'] = (program_end_time - program_start_time)
                        if variables_dict['verbosity'] > 3:
                            pkdr_utils.eprint('{} program execution pre db log insert'.format(code_block_times_dict['program_execution']))

                        pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
                        if (temperature > pkdr_utils.config_dict['temperature_valid_max'] or temperature < pkdr_utils.config_dict['temperature_valid_min']):
                            pkdr_utils.config_dict['db_table_dict']['val0'] += 'temperature->error->range'
                        elif (code_block_times_dict['program_execution'] > max_duration_program):
                            pkdr_utils.config_dict['db_table_dict']['val0'] += 'temperature->error->duration'
                        else:
                            pkdr_utils.config_dict['db_table_dict']['val0'] += 'temperature->error->or(range|duration)'

                        log_level = 4 # 4 = CRITICAL
                        pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
                        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level]
                        pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Sensor Range Error: {} < {} > {}'.format(pkdr_utils.config_dict['temperature_valid_min'], round(temperature, 3), pkdr_utils.config_dict['temperature_valid_max'])
                        # pkdr_utils.config_dict['db_table_dict']['key9'] = 'duration->program_execution'
                        # pkdr_utils.config_dict['db_table_dict']['val9'] = code_block_times_dict['program_execution']
                        pkdr_utils.db_variables_add_dict(code_block_times_dict)
                        pkdr_utils.db_generic_insert()
                    else:
                        program_end_time = time.time()
                        code_block_times_dict['program_execution'] = (program_end_time - program_start_time)
                        if variables_dict['verbosity'] > 3:
                            pkdr_utils.eprint('{} program execution'.format(code_block_times_dict['program_execution']))

    if variables_dict['verbosity'] > 3:
        for key, val in code_block_times_dict.items():
            if key != 'program_execution':
                if val > max_duration_block:
                    pkdr_utils.eprint('{} WARNING->DURATION: {} block took {} > {} second to complete'.format(str(datetime.datetime.now()), key, val, max_duration_block))
        
    # SQL for checking Thermostats table...
    # MariaDB [PkDr]> select apt, temperature as C, (temperature * 9/5) + 32 as F, taken from Thermostats order by uid desc limit 20;

# /usr/bin/python3 /home/PkDr/HA/code/PROD/python/pkdr_i2c_to_db.py -v 0 >> /home/pi/pkdr/logs/pkdr_i2c_to_db.log 


# --------------------------------------------------------------------------------
# useful stdout & stderr info
# https://www.cyberciti.biz/faq/linux-redirect-error-output-to-file/

# Syntax to redirect both output (stdout) and errors (stderr) to different files
# The syntax:

# command1 > out.txt 2> err.txt
# command2 -f -z -y > out.txt 2> err.txt
# Syntax to redirect both output (stdout) and errors (stderr) to same file
# The syntax is:

# command1 > everything.txt 2>&1

# Tip: Use tee command to redirect to both a file and the screen same time
# The syntax is:

# command1 |& tee log.txt
# ## or ##
# command1 -arg |& tee log.txt
# ## or ##
# command1 2>&1 | tee log.txt
# --------------------------------------------------------------------------------

# .log & .err
# /usr/bin/python3 /home/PkDr/HA/code/PROD/python/pkdr_i2c_to_db.py -v 0 >> /home/pi/pkdr/logs/i2c_to_db.log 2>> /home/pi/pkdr/logs/i2c_to_db.err

# redirect both to same .log
# /usr/bin/python3 /home/PkDr/HA/code/PROD/python/pkdr_i2c_to_db.py -v 4 >> /home/pi/pkdr/logs/i2c_to_db.log 2>&1


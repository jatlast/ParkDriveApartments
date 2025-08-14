#!/usr/bin/python

from __future__ import print_function # from __future__ imports must occur at the beginning of the file
#import sys # argv & python version
from sys import argv as my_argv, version_info as my_version_info, stderr as my_stderr
import os # program name from full path
import socket # needed for gethostname() & getsockname()
import re
from tkinter.tix import Tree # for regular expressions
import yaml # 20220213 Breaking out and consolidating config information to pkdr.yaml (pip install pyyaml)
import datetime # datestamps of program execution
import mysql.connector # for DB PkDr.RuntimeLog inserts

config_dict = {
    'error_msg' : '',
}

# function to allow programs to print directly to stderr...
# The optional function eprint saves some repetition. It can be used in the same way as the standard print function:
#   https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
# ---------------------------------------------
# from __future__ import print_function # SyntaxError: from __future__ imports must occur at the beginning of the file

def eprint(*args, **kwargs):
    print(*args, file=my_stderr, **kwargs)
# ---------------------------------------------

def initialize_config_dict(caller_dict):
    config_file = '/home/PkDr/HA/code/DEV/config/pkdr_config.yaml'
    error_flag = False

    global config_dict

    if caller_dict.get('verbosity', -1) == -1:
        caller_dict['verbosity'] = 0

    try:
        f = open(config_file, 'r')
    except OSError as err:
        error_flag = True
        config_dict['error_msg'] = "ERROR: pkdr_utils cannot open ("
        config_dict['error_msg'] += config_file
        config_dict['error_msg'] += ") due to OSError"
        if caller_dict['verbosity'] > 2:
            print("OS error: {0}".format(err))
    else:
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
        f.close()

    # Utility verbosity takes calling program's value unless changed by pkdr_config.yaml
    config_dict['verbosity'] = caller_dict['verbosity']

    get_calling_program_info(caller_dict)
    
    config_dict['config_file'] = config_file
    config_dict['error_flag'] = error_flag
    config_dict['error_msg'] = ''

    if not config_dict['error_flag']:
        # add caller defaluts
        config_dict['pkdr_id'] = ''
        config_dict['num_int'] = 0
        config_dict['num_str'] = '0'
        config_dict['pkdr_location_id'] = 'UNK'
        config_dict['mqtt_valid'] = False
        config_dict['mqtt_credentials_error_flag'] = False
        config_dict['mqtt_credentials_error_msg'] = ""
        config_dict['caller_error_flag'] = False
        config_dict['caller_error_msg'] = ""
        config_dict['program_valid'] = False
        config_dict['sensor_type_error_flag'] = False
        config_dict['sensor_temperature_window_error_flag'] = False
        config_dict['db_log_name'] = 'RuntimeLog'
        config_dict['db_insert_table'] = ''
        config_dict['log_level_name'] = 'INFO'
        config_dict['log_level'] = 1

        add_pkdr_caller_info_to_config_dict()

        # calling program takes utility's verbosity value after being initialized by pkdr_config.yaml
        #  verbosity override happens within function add_pkdr_caller_info_to_config_dict()
        caller_dict['verbosity'] = config_dict['verbosity']

        add_pkdr_mqtt_info_to_config_dict()

    return not config_dict['error_flag']

def get_calling_program_info(caller_dict):
    cli_options = ''
    for arg in my_argv[1:]:
        if ' ' in arg:
            cli_options += '"{}" '.format(arg) # spaces in options inplies option was quoted text
        else:
            cli_options += "{} ".format(arg)

    for key, value in caller_dict.items():
        config_dict['caller_{}'.format(key)] = value

    config_dict['ip'] = get_ip_address()
    config_dict['hostname'] = socket.gethostname()
    config_dict['utils_path'] = __file__
    config_dict['program_path'] = my_argv[0]
    config_dict['program_name'] = os.path.basename(my_argv[0])
    config_dict['program_options'] = cli_options
    config_dict['python_version_tuple'] = my_version_info
    config_dict['python_version'] =  '{}.{}.{}'.format(config_dict['python_version_tuple'].major, config_dict['python_version_tuple'].minor, config_dict['python_version_tuple'].micro)
    config_dict['datestamp'] = datetime.datetime.now()

def get_ip_address():
    ip_address = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))  # Google DNS
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

def get_hostname_apt_num():
    hostname = socket.gethostname()
    x = re.findall('apt(\d\d)', hostname)
    apt_num = int(x[0])
    return apt_num

# 20220214 - PkDr naming/numbering convension is currently: Apt## or B#
#   However, within Home Assistant's config files (apt## & Apt## & ##_) do get used.
#       I will try to rectify this during this 'HA Core' to 'HA OS' + 'PkDr DB' upgrade.
def add_pkdr_caller_info_to_config_dict():
    #global config_dict # unnecessary when called by function within the same script

    # Numbered 1 through 4 (0 & 5 are blank)
    config_dict['ip_as_list'] = re.split('(.*)\.(.*)\.(.*)\.(.*)', config_dict['ip'])

    caller_error_flag = False
    caller_error_msg = ""
    code_in_production_list = ""
    mqtt_topic_list = ""

    # try to set the pkdr_location_id variable
    if config_dict.get('ip_to_apt_dict', -1) == -1:
        caller_error_flag = True
        caller_error_msg += "Configuration Error: ip_to_apt_dict not in config file"
        config_dict['pkdr_location_id'] = 'err->ip_to_apt_dict'
    else:
        # integer format (apt = 1 to 16, bld = 41 to 44, # > 44 = last # of IP)
        config_dict['num_int'] = config_dict['ip_to_apt_dict'].get(config_dict['ip'], -1)
        if config_dict['num_int'] == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: IP not in config file ip_to_apt_dict"
            config_dict['pkdr_location_id'] = 'err->ip_to_apt_dict->ip'
        else:
            if config_dict['num_int'] <= 16:
                config_dict['pkdr_id'] = 'apt'
                config_dict['pkdr_location_id'] = 'Apt'
                if config_dict['num_int'] < 10:
                    config_dict['num_str'] = '0' + str(config_dict['num_int'])
                else:
                    config_dict['num_str'] = str(config_dict['num_int'])
                config_dict['pkdr_location_id'] += config_dict['num_str']
            elif config_dict['num_int'] <= 44 and config_dict['num_int'] > 40:
                config_dict['pkdr_id'] = 'bld'
                config_dict['pkdr_location_id'] = 'B' + str(config_dict['num_int'] % 40)
            else:
                caller_error_flag = True
                caller_error_msg += "ERROR: Number not an Apt or Bld"
                config_dict['pkdr_id'] = 'unk'
                config_dict['num_str'] = str(config_dict['num_int'])
                config_dict['pkdr_location_id'] = 'BorA'

# From Tasmota Config
# // -- MQTT topics ---------------------------------
# define MQTT_FULLTOPIC "PkDr/BorA/Room/%prefix%/%topic%/" // [FullTopic] Subscribe and Publish full topic name - Legacy topic

    # Valid MQTT against config file
    if len(config_dict['pkdr_location_id']) > 1 and config_dict['pkdr_location_id'] != 'BorA':
        if config_dict.get('mqtt_valid_topic_location_list', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: mqtt_valid_topic_location_list not in config file"
        else:
            mqtt_topic_list = "MQTT Topic Search <"
            for i in config_dict["mqtt_valid_topic_location_list"]:
                if config_dict['pkdr_location_id'] == i:
                    if config_dict['verbosity'] > 2:
                        mqtt_topic_list += "({}) == ({}) - Found".format(config_dict['pkdr_location_id'], i)
                    config_dict['mqtt_valid'] = True
                    break
                else:
                    mqtt_topic_list += "({}) != ({})".format(config_dict['pkdr_location_id'], i)
            mqtt_topic_list += ">"
            if config_dict['verbosity'] > 3:
                print(mqtt_topic_list)

    # Valid Production Code Config Check
    if config_dict.get('production_code_config', -1) == -1:
        caller_error_flag = True
        caller_error_msg += "Configuration Error: production_code_config not in config file"
    else:
        # Logging defaults and overrides
        if config_dict['production_code_config'].get('runtime_logging_config', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: runtime_logging_config"
        elif config_dict['production_code_config']['runtime_logging_config'].get('log_level_default', -1) == -1 or config_dict['production_code_config']['runtime_logging_config'].get('log_level_override', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: log_level_default | log_level_override not in config file"
        elif config_dict['production_code_config']['runtime_logging_config']['log_level_default'].get('name', -1) == -1 or config_dict['production_code_config']['runtime_logging_config']['log_level_default'].get('number', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: log_level_default.name | log_level_default.number not in config file"
        elif config_dict['production_code_config']['runtime_logging_config']['log_level_default'].get('name', -1) == -1 or config_dict['production_code_config']['runtime_logging_config']['log_level_override'].get('number', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: log_level_override.name | log_level_override.number not in config file"
        else:
            # Set the overrides...
            config_dict['log_level_name'] = config_dict['production_code_config']['runtime_logging_config']['log_level_default']['name']
            config_dict['log_level'] = config_dict['production_code_config']['runtime_logging_config']['log_level_default']['number']

            if config_dict['production_code_config']['runtime_logging_config']['log_level_override']['enable']:
                # Set the defaults...
                config_dict['log_level_name'] = config_dict['production_code_config']['runtime_logging_config']['log_level_override']['name']
                config_dict['log_level'] = config_dict['production_code_config']['runtime_logging_config']['log_level_override']['number']

        # Debug Verbosity Check
        if config_dict['production_code_config'].get('verbosity_override_flag', -1) == -1 or config_dict['production_code_config'].get('verbosity_override_value', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: verbosity_override_flag | verbosity_override_value not in config file"
        else:
            if config_dict['production_code_config']['verbosity_override_flag'] and config_dict['verbosity'] != config_dict['production_code_config']['verbosity_override_value']:
                print("{}: Changed Verbosity {} to {}".format(config_dict['datestamp'], config_dict['verbosity'], config_dict['production_code_config']['verbosity_override_value']), flush=True)
                config_dict['verbosity'] = config_dict['production_code_config']['verbosity_override_value']

        # Production Code Check
        if config_dict['production_code_config'].get('code_in_production_list', -1) == -1:
            caller_error_flag = True
            caller_error_msg += "Configuration Error: code_in_production_list not in config file"
        else:
            # Check the config file to see if the code is in production...
            code_in_production_list = "Production Code Search <"
            for i in config_dict['production_code_config']["code_in_production_list"]:
                if config_dict['program_name'] == i:
                    config_dict['program_valid'] = True
                    if config_dict['verbosity'] > 2:
                        code_in_production_list += "({}) == ({}) - Found".format(config_dict['program_name'], i)
                    break
                else:
                    code_in_production_list += "({}) != ({})".format(config_dict['program_name'], i)
            code_in_production_list += ">"

        # 20220215 - Decided not to implement FAIL IF python version checking. The below is as far as I got
        # --------------
        if config_dict['production_code_config'].get('fail_if_not_in_production', -1) == -1:
            config_dict['production_code_config']['fail_if_not_in_production'] = False
            caller_error_flag = True
            caller_error_msg += "Configuration Error: fail_if_not_in_production not in config file"

        if config_dict['production_code_config'].get('fail_if_version_less_major', -1) == -1:
            config_dict['production_code_config']['fail_if_version_less_major'] = False
            caller_error_flag = True
            caller_error_msg += "Configuration Error: fail_if_version_less_major not in config file"
            
        if config_dict['production_code_config'].get('fail_if_version_less_minor', -1) == -1:
            config_dict['production_code_config']['fail_if_version_less_minor'] = False            
            caller_error_flag = True
            caller_error_msg += "Configuration Error: fail_if_version_less_minor not in config file"

        # if config_dict['production_code_config']['fail_if_version_less_major'] and config_dict['python_version_tuple'].major :
        #     # calling scripts should kill themselves when encountering the config_dict['error_flag']...
        #     config_dict['error_flag'] = True
        #     config_dict['error_msg'] += code_in_production_list
        # --------------

    config_dict['sensor_type_error_flag'] = False
    # Check for temperature sensor dict...
    if config_dict.get('sensor_config', -1) == -1:
        config_dict['sensor_type_error_flag'] = True
        caller_error_flag = True
        caller_error_msg += "Configuration Error: sensor_config not in config file"
    else:
        # Check for sound files dict...
        if config_dict['sensor_config'].get('i2c_temperature_config', -1) == -1:
            config_dict['sensor_type_error_flag'] = True
            caller_error_flag = True
            caller_error_msg += "Configuration Error: i2c_temperature_config not in config file"
        else:
            # Check for temperature sensor dict...
            if config_dict['sensor_config']['i2c_temperature_config'].get('ip_to_temperature_sensor_dict', -1) == -1:
                config_dict['sensor_type_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: ip_to_temperature_sensor_dict not in config file"
            else:
                # (HTU21D or SHT31D or SHT4xD)
                sensor_type = config_dict['sensor_config']['i2c_temperature_config']['ip_to_temperature_sensor_dict'].get(config_dict['ip'], -1)
                if sensor_type == -1:
                    config_dict['sensor_type_error_flag'] = True
                else:
                    config_dict['sensor_type'] = sensor_type
                    # (HTU21D:0x40 or SHT31D:0x44 or SHT4xD:0x44)
                    sensor_type_address = config_dict['sensor_config']['i2c_temperature_config']['i2c_sensor_type_to_address'].get(config_dict['sensor_type'], -1)
                    if sensor_type_address == -1:
                        config_dict['sensor_type_error_flag'] = True
                    else:
                        config_dict['sensor_type_address'] = sensor_type_address

            # Check for temperature window dict...
            if config_dict['sensor_config']['i2c_temperature_config'].get('temperature_window', -1) == -1:
                config_dict['sensor_temperature_window_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: temperature_window not in config file"
            else:
                temperature_valid_min = config_dict['sensor_config']['i2c_temperature_config']['temperature_window'].get('temperature_valid_min', -1)
                if temperature_valid_min == -1:
                    config_dict['sensor_temperature_window_error_flag'] = True
                else:
                    config_dict['temperature_valid_min'] = temperature_valid_min
                    temperature_valid_max = config_dict['sensor_config']['i2c_temperature_config']['temperature_window'].get('temperature_valid_max', -1)
                    if temperature_valid_max == -1:
                        config_dict['sensor_temperature_window_error_flag'] = True
                    else:
                        config_dict['temperature_valid_max'] = temperature_valid_max


    # Check for sound files dict...
    config_dict['sound_config_error_flag'] = False
    # Check for temperature sensor dict...
    if config_dict.get('sound_config', -1) == -1:
        config_dict['sound_config_error_flag'] = True
        caller_error_flag = True
        caller_error_msg += "Configuration Error: sensor_config not in config file"
    else:
        # Check for sound files dict...
        if config_dict['sound_config'].get('sound_path', -1) == -1:
            config_dict['sound_config_error_flag'] = True
            caller_error_flag = True
            caller_error_msg += "Configuration Error: sound_path not in config file"

        if config_dict['sound_config'].get('sound_files_dict', -1) == -1:
            config_dict['sound_config_error_flag'] = True
            caller_error_flag = True
            caller_error_msg += "Configuration Error: sound_files_dict not in config file"
        else:
            if config_dict['sound_config']['sound_files_dict'].get('system_start', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: system_start not in config file"
            if config_dict['sound_config']['sound_files_dict'].get('doorbell_main', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: doorbell_main not in config file"
            if config_dict['sound_config']['sound_files_dict'].get('doorbell_alt_1', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: doorbell_alt_1 not in config file"
            if config_dict['sound_config']['sound_files_dict'].get('doorbell_alt_2', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: doorbell_alt_2 not in config file"
            if config_dict['sound_config']['sound_files_dict'].get('doorbell_alt_3', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: doorbell_alt_3 not in config file"
            if config_dict['sound_config']['sound_files_dict'].get('doorbell_alt_4', -1) == -1:
                config_dict['sound_config_error_flag'] = True
                caller_error_flag = True
                caller_error_msg += "Configuration Error: doorbell_alt_4 not in config file"

    config_dict['caller_error_flag'] = caller_error_flag
    config_dict['caller_error_msg'] = caller_error_msg

    # initialize the DB Log prior to using it and after the necessary DB variables have been gathered from the config yaml
    db_table_dict_init(config_dict['db_log_name'])

    # Log problems encountered in this function to DB...
    if caller_error_flag:
        config_dict['log_level'] = 4 # 4 = CRITICAL
        config_dict['db_table_dict']['log_message'] = caller_error_msg
        db_generic_insert(config_dict['db_log_name'])

    # Log Production Code Names issues to DB...
    if not config_dict['program_valid']:
        # Check suicide flags
        if config_dict['production_code_config']['fail_if_not_in_production']:
            # calling scripts should kill themselves when encountering the config_dict['error_flag']...
            config_dict['error_flag'] = True
            config_dict['error_msg'] += code_in_production_list
        config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][2] # 2 = WARNING
        config_dict['db_table_dict']['log_message'] = code_in_production_list
        db_generic_insert(config_dict['db_log_name'])

    # Log MQTT Config issues to DB...
    if not config_dict['mqtt_valid']:
        config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][2] # 2 = WARNING
        config_dict['db_table_dict']['log_message'] = mqtt_topic_list
        db_generic_insert(config_dict['db_log_name'])

def add_pkdr_mqtt_info_to_config_dict():
    mqtt_credentials_error_flag = False
    mqtt_credentials_error_msg = ""

    mqtt_credentials_error_flag = False
    # pkdr mqtt config
    if config_dict.get('pkdr_mqtt_config', -1) == -1:
        mqtt_credentials_error_flag = True
        mqtt_credentials_error_msg += "Configuration Error: pkdr_mqtt_config not in config file"
    else:
        # paho client
        if config_dict['pkdr_mqtt_config'].get('paho_client_dict', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: paho_client_dict not in config file"
        # paho log level lookup number to name dict
        elif config_dict['pkdr_mqtt_config']['paho_client_dict'].get('log_levels_dict', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: log_levels_dict not in config file"
        # paho log level lookup name to log-if value
        elif config_dict['pkdr_mqtt_config']['paho_client_dict'].get('log_levels_if_dict', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: log_levels_if_dict not in config file"

        # mosquitto broker
        if config_dict['pkdr_mqtt_config'].get('mosquitto_broker_config', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: mosquitto_broker_config not in config file"
        # mosquitto broker credentials dict
        elif config_dict['pkdr_mqtt_config']['mosquitto_broker_config'].get('credentials_dict', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: credentials_dict not in config file"

        # relay cong dict for Building Kiosks
        if config_dict['pkdr_mqtt_config'].get('pkdr_id_to_mqtt_dict', -1) == -1:
            mqtt_credentials_error_flag = True
            mqtt_credentials_error_msg += "Configuration Error: pkdr_id_to_mqtt_dict not in config file"

    config_dict['mqtt_credentials_error_flag'] = mqtt_credentials_error_flag
    config_dict['mqtt_credentials_error_msg'] = mqtt_credentials_error_msg

def db_table_dict_init(table_name = 'RuntimeLog'):
    # Thermostats | RuntimeLog (default) as of 20220215
    config_dict['db_insert_dict'] = {}

    if table_name == config_dict['db_log_name']:
        if config_dict.get('db_table_dict', -1) == -1:
            config_dict['db_table_dict'] = {
                'author_date' : str(config_dict['datestamp']),
                'author_name' : '{}'.format(config_dict['hostname']),
                # ToDo: Remove the name from the path
                'author_path' : '{}'.format(config_dict['program_path']),
                'author_options' : '{}'.format(config_dict['program_options']),
                'author_address' : '{}'.format(config_dict['ip']),
                'author_version' : '{}'.format(config_dict['python_version']),
                'log_level' : config_dict['log_level'],
                'log_level_name' : config_dict['log_level_name'],
                'log_message' : '',
                'exception_type' : '',
                'exception_text' : '',
                'query_text' : '',
                'query_attempts' : 0,
                # 20220222 - new key0 convention to help with future SQL digging for log data...
                # Note: key0 & val0 usage convention in progress...
                # key0 = 'log_key' to signify val0 = 'info_about->something->something_more'
                'key0' : 'key_log',
                'val0' : 'script_did_not_set', # shoud be set by script to supply why the message was logged
                'key1' : 'pkdr_id',
                'val1' : '{}'.format(config_dict['pkdr_location_id']), # [Apt## || B#]
            }
        else:
            config_dict['db_table_dict']['query_attempts'] += 1

def db_table_dict_init_force():
    config_dict['db_table_dict'] = -1
    db_table_dict_init()

def db_variables_add_dict(key_value_pair_dict):
    insert_failed_flag = False
    key_passed_to_key_used_dict = {}
    key_used_temp = ''
    for key, value in key_value_pair_dict.items():
        key_used_temp = db_variables_add_key_value(key, value)
        if len(key_used_temp) < 3:
            key_passed_to_key_used_dict[key] = ''
            insert_failed_flag = True
            break
        else:
            key_passed_to_key_used_dict[key] = key_used_temp
    return key_passed_to_key_used_dict

def db_variables_add_key_value(key, value):
    db_variable_total = 10 # key0 & key1 are spoken for by convention
    key_name = ''
    insert_failed_flag = True
    # make a list containing variable key names to match the db variable names
    for i in range(db_variable_total):
        if i > 1:
            key_name = 'key{}'.format(str(i))
            if config_dict['db_table_dict'].get(key_name, -1) == -1:
                config_dict['db_table_dict'][key_name] = key
                config_dict['db_table_dict']['val' + str(i)] = value
                insert_failed_flag = False
                break
            else:
                if config_dict['verbosity'] > 3:
                    print("key {} unavailable".format(key_name))
                key_name = ''
        else:
            pass # key0 and key1 are spoken for by convention
    
    debug_text = ''
    if insert_failed_flag:
        debug_text = "Failed:  db_variables_add_key_value({}, {})".format(key, value)
    else:
        debug_text = "Success: db_variables_add_key_value({}, {}) used {}".format(key, value, key_name)

    if config_dict['verbosity'] > 3:
        print("{}: {}".format(config_dict['datestamp'], debug_text))

    return key_name

# select val0, count(*) from RuntimeLog where key0 = 'log_key' group by val0;
# +----------------------------------+----------+
# | val0                             | count(*) |
# +----------------------------------+----------+
# | sensor->exception->set_generic   |        2 |
# | sensor->temperature->range_error |        9 |
# | sensor->type_or_address          |        1 |
# +----------------------------------+----------+

def db_generic_insert(table_name = 'RuntimeLog'):
    config_dict['db_error_msg'] = ""
    config_dict['db_error_flag'] = False

    # The log level might be changed before this function calls the database
    # config_dict['db_table_dict']['log_level'] = config_dict['log_level']
    # config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][config_dict['db_table_dict']['log_level']]

    column_count = 0
    query_column_list = []
    query_values_list = []
    if table_name == config_dict['db_log_name']:
        db_table_dict_init(table_name) # initialize the config for a logfile insers
        for key, value in config_dict['db_table_dict'].items():
            query_column_list.append(key)
            query_values_list.append(value)
            column_count += 1
    else:
        config_dict['db_insert_table'] = table_name
        for key, value in config_dict['db_insert_dict'].items():
            query_column_list.append(key)
            query_values_list.append(value)
            column_count += 1

        if(config_dict['verbosity'] > 3):
            print("Ignoring: col=({}), val=({}), len=({})".format(key, value, len(value)))
            # print(key, ":", value)

    # With constructed lists excluding empty values...
    query_insert = "INSERT INTO {table} ({columns}) VALUES {values};".format(
                table = table_name,
                columns = ', '.join(query_column_list),
                values = tuple(query_values_list)
            )

    if config_dict['verbosity'] > 2:
        print("{}: SQL {}".format(config_dict['datestamp'], query_insert))

    # if config_dict['db_table_dict']['query_attempts'] > config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_insert_attempts_max']:
        # Check if dynamic table is being called
        # if config_dict['db_dynamic_table_dict']['query_attempts'] > 0:

    if config_dict['db_table_dict']['query_attempts'] > config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_insert_attempts_max']:
        print("{}: DB Call Recursion Error: attempts ({}) > max ({}) | SQL: {}".format(config_dict['datestamp'], config_dict['db_table_dict']['query_attempts'], config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_insert_attempts_max'], query_insert))
        # reset recursion variables...
        config_dict['db_error_flag'] = False
        config_dict['db_table_dict']['query_attempts'] = 0
    else:
        try:
            connection = mysql.connector.connect(
                host = config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_host_ip"],
                database = config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_name"],
                user = config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_user"],
            )

            cursor = connection.cursor()
            cursor.execute(query_insert)
            connection.commit()
            # Succcess
            if cursor.rowcount > 0:
                if config_dict['verbosity'] > 1:
                    print("{}: DB Success: {} insert into {} table".format(config_dict['datestamp'], cursor.rowcount, table_name))
            # Failure
            else:
                config_dict['db_error_flag'] = True
                config_dict['log_level'] = 3 # 3 = ERROR
                config_dict['db_table_dict']['log_level'] = config_dict['log_level']
                config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][config_dict['db_table_dict']['log_level']]
                config_dict['db_error_msg'] += "DB Fail: Unable to insert into {} table".format(table_name)
                if config_dict['verbosity'] >= 0:
                    print("{}: DB Error: {} | SQL: {}".format(config_dict['datestamp'], config_dict['db_error_msg'], query_insert))

                cursor.close()

        # Couldn't connect to the DB
        # except mysql.connector.Error as error: # 20220222 - replaced with generic catch
        except BaseException as err:
            config_dict['db_error_msg'] = "DB Error: Failed to insert into table {} | connection = mysql.connector.connect(host={},database={},user={},) - raised exception ({})|({})".format(table_name, config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_host_ip"], config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_name"], config_dict['pkdr_remote_db_config']['db_credentials_dict']["db_user"], type(err), err)
            config_dict['db_error_flag'] = True
            config_dict['log_level'] = 4 # 4 = CRITICAL
            config_dict['db_table_dict']['log_level'] = config_dict['log_level']
            config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][config_dict['db_table_dict']['log_level']]
            if config_dict['verbosity'] >= 0:
                print('{}: {}'.format(config_dict['datestamp'], config_dict['db_error_msg']))

        # Catch DB Error and log the error to RuntimeLog table
        if config_dict['db_error_flag']:
            # Always try adding the current query to the RuntimeLog column query_text
            if config_dict['db_table_dict'].get('query_text', -1) == -1:
                config_dict['db_table_dict']['query_text'] = query_insert
            # Check if the previous querytext is the same as the current querytext
            elif config_dict['db_table_dict']['query_text'] == query_insert:
                print("Current Insert was already attempted: {}".format(query_insert))

            if config_dict['db_table_dict'].get('log_message', -1) == -1:
                config_dict['db_table_dict']['log_message'] = config_dict['db_error_msg']
            else:
                config_dict['db_table_dict']['log_message'] += ' <append> ' + config_dict['db_error_msg']

            if config_dict.get('db_insert_table', -1) != -1:
                db_variables_add_key_value('db_table', config_dict['db_insert_table'])

            # Use recursion to log any errors that happened within this function...
            db_generic_insert(config_dict['db_log_name'])
        else:
            # clear db_table_dict
            db_table_dict_init(config_dict['db_log_name'])

def print_caller_info():
    print('--------------- Caller Info ---------------')
    if config_dict.get('program_name', -1) != -1:
        print("datestamp = {}".format(config_dict['datestamp']))
        print("ip = {}".format(config_dict['ip']))
        print("hostname = {}".format(config_dict['hostname']))
        print("program_name = {}".format(config_dict['program_name']))
        print("utils_path = {}".format(config_dict['utils_path']))
        print("program_path = {}".format(config_dict['program_path']))
        print("program_options = {}".format(config_dict['program_options']))
        print("python_version = {}".format(config_dict['python_version']))
    print('-------------------------------------------')

# The purpose of the '__main__' check is to determine if the code is being executed by external code
#   If the code is being executed by external code, any code outside of the 'if __name__' block will be executed
#   However, any code inside of the 'if __name__' block will not be executed
def main():
    empty_dict = {}
    initialize_config_dict(empty_dict)
    if config_dict.get('program_name', -1) != -1:
        print("NOTICE: {} is a utility script not meant to be executed directly.".format(config_dict['program_name']))
        print_caller_info()
        config_dict['log_level'] = 1 # 1 = INFO
        config_dict['db_table_dict']['log_level'] = config_dict['log_level']
        config_dict['db_table_dict']['log_level_name'] = config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][config_dict['db_table_dict']['log_level']]
        config_dict['db_table_dict']['log_message'] = "NOTICE: {} was executed as an independent script instead of a utility script".format(config_dict['program_name'])
        config_dict['db_table_dict']['val0'] = 'utils->test'
        db_generic_insert()
        print("Contents of the pkdr_utils.config_dict:")
        for key, val in config_dict.items():
            print("{} = {}".format(key, val))
    else:
        print("Configuration Error: unable to initialize the pkdr_utils.config_dict")

if __name__ == "__main__":
    main()

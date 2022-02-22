#!/usr/bin/env python

# ------------
# JTB 20220213
# ------------
# This code is (or will be) required by ...
#   PkDr Kiosks: Apt 01 - 16
# The code ...
#   - depends on config/secrets.yaml
#   - depends on pkdr_utils.py
#   - runs in-place on the NAS drive
#   - runs as a service on Raspberry Pi boxes with Rasbian OS installed
# The Service ...
#   - configuration location
#       /etc/systemd/system/pkdr_kiosk_doorbell.service
#   - can be managed using systemctl to (stop, start, restart, enable, disable, etc)
# ------------

import time # needed to sleep the listening loop
import vlc # needed to play doorbell .wav file
import paho.mqtt.client as mqtt # needed to listen for MQTT messages
    # https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php
import datetime # needed for now()
import argparse # allow command line options
import pkdr_utils # (JTB Script as Util) loads the local configurations for all PkDr Scripts

# mqtt.Client.is_connected

parser = argparse.ArgumentParser(description="Listen for MQTT message asking for the doorbell to ring then use VLC to play a dorbell sound")
parser.add_argument(
    "-v",
    "--verbosity",
    type=int,
    choices=[0, 1, 2, 3, 4],
    default=0,
    help="increase output verbosity",
)
args = parser.parse_args()

variables_dict = {
    "program_name": parser.prog,
    "verbosity": args.verbosity,
    "sleep_in_loop": 0.50,
    "sleep_after_vlc": 10.00,  # allow time to play the full media file
    # The suscribe method accepts 2 parameters.  Note: can suscribe to more than one topic at a time.
    #    subscribe(topic, qos=0)
    "doorbell_volume": 60,  # 60 is the default volume setting
    "mqtt_subscribe_qos": 1,
    # The message payload that triggers the action of this program
    "actionable_payload": "CHIME",
    "sound_played": "",
    "action_previous_datetime": datetime.datetime.now(),
}

log_level = 10 # Dummy Number
runtime_messages = ''
runtime_error_message = ''
runtime_error_flag = False

def on_disconnect(client, userdata, rc):
    global runtime_message
    runtime_message = "def on_disconnect() result code = ({})".format(rc)
    if variables_dict["verbosity"] > 2:
        print('K-VDB-Runtime: '.format(runtime_messages))
    # logging.debug("DisConnected result code " + str(rc))
    client.loop_stop()

# Note the message parameter is a message class with members: topic, qos, payload, retain.
def on_message(client, userdata, message):
    global runtime_message, runtime_error_message
    runtime_messages = ' on_message() '
    action_current_datetime = datetime.datetime.now()

    # check the volume first...
    if message.topic == variables_dict["mqtt_subscribe_volume"]:
        runtime_messages += "INFO: doorbell_volume changed from {} to {}\n".format(variables_dict["doorbell_volume"])
        variables_dict["doorbell_volume"] = str(message.payload.decode("utf-8"))
        runtime_messages += "INFO: {} Topic: {} | Payload: {}".format(action_current_datetime,message.topic)

    if (str(message.payload.decode("utf-8")) == variables_dict["actionable_payload"]):

        action_duration = (action_current_datetime - variables_dict["action_previous_datetime"])

        # reset the previous action variable
        variables_dict["action_previous_datetime"] = action_current_datetime

        # Duration in seconds
        seconds = action_duration.total_seconds()
        # Duration in years
        years = divmod(seconds, 31536000)[0]  # Seconds in a year=365*24*60*60 = 31536000.
        # Duration in days
        days = action_duration.days  # Built-in datetime function
        #        days = divmod(seconds, 86400)[0]       # Seconds in a day = 86400
        # Duration in hours
        hours = divmod(seconds, 3600)[0]  # Seconds in an hour = 3600
        # Duration in minutes
        minutes = divmod(seconds, 60)[0]  # Seconds in a minute = 60

        # black pkdr_kiosk_doorbell.py --target-version py39 --verbose --config FILE

        if seconds > 60:
            variables_dict['sound_played'] = variables_dict['sound_1']
        elif seconds > 30:
            variables_dict['sound_played'] = variables_dict['sound_2']
        elif seconds > 20:
            variables_dict['sound_played'] = variables_dict['sound_3']
        elif seconds > variables_dict['sleep_after_vlc']:
            variables_dict['sound_played'] = variables_dict['sound_4']
        else:
            variables_dict['sound_played'] = variables_dict['sound_patience']

        vlc_player = vlc.MediaPlayer(variables_dict['sound_played'])
        # https://www.geeksforgeeks.org/python-vlc-mediaplayer-setting-volume/
        vlc_player.audio_set_volume(variables_dict['doorbell_volume'])
        # vlc_player.audio_set_volume(80)
        vlc_player.play()
        time.sleep(variables_dict['sleep_after_vlc'])

        # the stop() is required to prevent orphaned vlc player objects
        vlc_player.stop()

        duration_since_last_doorbell = "Duration: seconds {} | minutes {} | hours {} | days {} | years {} | ".format(seconds, minutes, hours, days, years)
        if variables_dict['verbosity'] > 0:
            print(duration_since_last_doorbell)
            print("K-VDB-Runtime: {} | Found: {} | Payload: {} | Topic: {} | Played: {}".format(datetime.datetime.now(), variables_dict['actionable_payload'], str(message.payload.decode("utf-8")), message.topic, variables_dict['sound_played']))

        # Log the doorbell ring...
        msg_log_level = 1 # INFO
        pkdr_utils.config_dict['db_table_dict']['log_level'] = msg_log_level
        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][msg_log_level]
        pkdr_utils.config_dict['db_table_dict']['log_message'] = 'Doorbell Chime'
        pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
        pkdr_utils.config_dict['db_table_dict']['val0'] = 'doorbell->mqtt->found_payload'
        pkdr_utils.config_dict['db_table_dict']['key2'] = 'mqtt_apt_or_bld'
        pkdr_utils.config_dict['db_table_dict']['val2'] = pkdr_utils.config_dict['mqtt_topic_apt_or_bld']
        pkdr_utils.config_dict['db_table_dict']['key3'] = 'topic'
        pkdr_utils.config_dict['db_table_dict']['val3'] = message.topic
        pkdr_utils.config_dict['db_table_dict']['key4'] = 'payload'
        pkdr_utils.config_dict['db_table_dict']['val4'] = variables_dict['actionable_payload']
        pkdr_utils.config_dict['db_table_dict']['key5'] = 'sound_played'
        pkdr_utils.config_dict['db_table_dict']['val5'] = variables_dict['sound_played']
        pkdr_utils.config_dict['db_table_dict']['key6'] = 'doorbell_volume'
        pkdr_utils.config_dict['db_table_dict']['val6'] = variables_dict["doorbell_volume"]
        pkdr_utils.config_dict['db_table_dict']['key7'] = 'time_since_previous'
        pkdr_utils.config_dict['db_table_dict']['val7'] = duration_since_last_doorbell
        pkdr_utils.db_generic_insert()

def on_log(client, userdata, level, buf):
    log_if_less_or_equal_level = pkdr_utils.config_dict['pkdr_mqtt_config']['paho_client_dict'].get('log_if_less_or_equal_level', -1)
    if log_if_less_or_equal_level <= level:
        log_level = 1 # 1 = INFO
        pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
        # pkdr_utils.config_dict['db_table_dict']['log_message'] = "on_log(client, userdata={}, level={} buf={})".format(userdata, level, buf)
        pkdr_utils.config_dict['db_table_dict']['log_message'] = 'MQTT Runtime Log'
        pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
        pkdr_utils.config_dict['db_table_dict']['val0'] = 'doorbell->mqtt->on_log'
        pkdr_utils.config_dict['db_table_dict']['key2'] = 'log_if_less_or_equal_level'
        pkdr_utils.config_dict['db_table_dict']['val2'] = log_if_less_or_equal_level
        pkdr_utils.config_dict['db_table_dict']['key3'] = 'level_lookup'
        pkdr_utils.config_dict['db_table_dict']['val3'] = pkdr_utils.config_dict['pkdr_mqtt_config']['paho_client_dict']['log_levels_dict'].get(level, 'Lookup failed for level=({})'.format(level))
        pkdr_utils.config_dict['db_table_dict']['key4'] = 'level'
        pkdr_utils.config_dict['db_table_dict']['val4'] = level
        pkdr_utils.config_dict['db_table_dict']['key5'] = 'mqtt_callback'
        pkdr_utils.config_dict['db_table_dict']['val5'] = 'def on_log(client, userdata, level, buf)'
        pkdr_utils.config_dict['db_table_dict']['key6'] = 'buf'
        pkdr_utils.config_dict['db_table_dict']['val6'] = buf
        pkdr_utils.db_generic_insert()
        if variables_dict["verbosity"] > 1:
            print('K-VDB-Runtime: '.format(pkdr_utils.config_dict['db_table_dict']['log_message']))
    else:
        if variables_dict["verbosity"] > 2:
            print('Not Logged: log if {} > level {}'.format(log_if_less_or_equal_level, level))

# -------------------------------------------
# ----- Program Execution Block - Start -----
# -------------------------------------------

# ----- Initialize using PkDr Utils -----
if not pkdr_utils.initialize_config_dict(variables_dict):
    print("{}: Configuration Failure ({})".format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['error_msg']))
# ---------------------------------------
elif (
        not pkdr_utils.config_dict['mqtt_valid']
        or pkdr_utils.config_dict['mqtt_credentials_error_flag']
        or pkdr_utils.config_dict['sound_config_error_flag']
    ):
    log_level = 4 # 4 = CRITICAL
    pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
    pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
    pkdr_utils.config_dict['db_table_dict']['log_message'] = 'VDB Config Error: '
    pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
    pkdr_utils.config_dict['db_table_dict']['val0'] = 'doorbell->config->error'

    if not pkdr_utils.config_dict['mqtt_valid'] or pkdr_utils.config_dict['sound_config_error_flag']:
        pkdr_utils.config_dict['db_table_dict']['log_message'] += pkdr_utils.config_dict['caller_error_msg']
    elif pkdr_utils.config_dict['mqtt_credentials_error_flag']:
        pkdr_utils.config_dict['db_table_dict']['log_message'] += pkdr_utils.config_dict['mqtt_credentials_error_msg']
 
    # log the error
    pkdr_utils.db_generic_insert()
else:
    # add_pkdr_mqtt_info_to_config_dict() should probably be in this proc and not global
    # pkdr_utils.add_pkdr_mqtt_info_to_config_dict()

    # mqtt_same_as_home_assistant = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('same_as_home_assistant', -1)
    # if mqtt_same_as_home_assistant != -1:
    #     if mqtt_same_as_home_assistant:
    #         variables_dict['pkdr_mqtt_ip'] = pkdr_utils.config_dict['mqtt_broker_ip']
    #         variables_dict['pkdr_mqtt_port'] = pkdr_utils.config_dict['mqtt_broker_port']
    #         variables_dict['pkdr_mqtt_un'] = pkdr_utils.config_dict['mqtt_username']
    #         variables_dict['pkdr_mqtt_pw'] = pkdr_utils.config_dict['mqtt_password']
    # else:
    variables_dict['pkdr_mqtt_ip'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_broker_ip', 'KeyError')
    variables_dict['pkdr_mqtt_port'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_broker_port', 'KeyError')
    variables_dict['pkdr_mqtt_un'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_username', 'KeyError')
    variables_dict['pkdr_mqtt_pw'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_password', 'KeyError')

    variables_dict['sound_1'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_main']

    variables_dict['sound_2'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
    variables_dict['sound_3'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_2']
    variables_dict['sound_4'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
    variables_dict['sound_patience'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['system_start']

    variables_dict["mqtt_subscribe_topic"] = ("PkDr/" + pkdr_utils.config_dict['mqtt_topic_apt_or_bld'] + "/Entrance/cmnd/Doorbell/POWER")
    variables_dict["mqtt_subscribe_volume"] = ("PkDr/" + pkdr_utils.config_dict['mqtt_topic_apt_or_bld'] + "/Doorbell/stat/Volume/setVolume")
    variables_dict["pkdr_mqtt_client"] = pkdr_utils.config_dict['mqtt_topic_apt_or_bld']

    runtime_messages += "INFO: Topic Location: ({})\n".format(pkdr_utils.config_dict['mqtt_topic_apt_or_bld'])
    runtime_messages += "INFO: MQQT Doorbell Topic: ({})\n".format(variables_dict["mqtt_subscribe_topic"])
    runtime_messages += "INFO: MQQT Volume Topic: ({})\n".format(variables_dict["mqtt_subscribe_volume"])

    if variables_dict["verbosity"] > 0:
        print('K-VDB-Runtime: '.format(runtime_messages))

#        pkdr_mqtt_client.publish(variables_dict['mqtt_subscribe_topic'], payload=variables_dict['actionable_payload_reset'], qos=variables_dict['mqtt_publish_qos'], retain=variables_dict['mqtt_publish_retain'])
#        time.sleep(variables_dict['loop_sleep'])

    pkdr_mqtt_client = mqtt.Client(variables_dict["pkdr_mqtt_client"])  # create client object

    # bind to the on_message function because this is where this script logic lives
    pkdr_mqtt_client.on_message = on_message

    pkdr_mqtt_client.on_log = on_log

    # print("mqtt user ({}) pw ({})".format(variables_dict["pkdr_mqtt_un"], variables_dict["pkdr_mqtt_pw"]))
    pkdr_mqtt_client.username_pw_set(username=variables_dict["pkdr_mqtt_un"],password=variables_dict["pkdr_mqtt_pw"])

    exception_msg = ''
    exception_type = ''
    exception_flag = False
    try:
        # 20220220 - try to connect
        # connect(host, port=1883, keepalive=60, bind_address="")
        pkdr_mqtt_client.connect(variables_dict["pkdr_mqtt_ip"], variables_dict["pkdr_mqtt_port"])  # establish connection
    except OSError as err:
        exception_type = '{}'.format(type(err))
        exception_msg = 'Exception pkdr_mqtt_client.connect(host={}, port={}) raised: OSError {}'.format(variables_dict["pkdr_mqtt_ip"], variables_dict["pkdr_mqtt_port"], err)
        exception_flag = True
    except Exception as err:
        exception_type = '{}'.format(type(err))
        exception_msg = 'Exception pkdr_mqtt_client.connect(host={}, port={}) raised: Unexptected ({})|({}) - This should never happen'.format(variables_dict["pkdr_mqtt_ip"], variables_dict["pkdr_mqtt_port"], type(err), err)
        pkdr_utils.config_dict['db_table_dict']['log_message'] = 'CODE: {} requires updating'.format(pkdr_utils.config_dict['program_path'])
        exception_flag = True

    # ----- Log Conifuration Errors to DB -----
    if exception_flag:
        log_level = 4 # 4 = CRITICAL
        pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
        pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
        pkdr_utils.config_dict['db_table_dict']['exception_type'] = exception_type
        pkdr_utils.config_dict['db_table_dict']['exception_text'] = exception_msg
        pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
        pkdr_utils.config_dict['db_table_dict']['val0'] = 'doorbell->exception'
        pkdr_utils.config_dict['db_table_dict']['key2'] = 'pkdr_mqtt_ip'
        pkdr_utils.config_dict['db_table_dict']['val2'] = variables_dict["pkdr_mqtt_ip"]
        pkdr_utils.config_dict['db_table_dict']['key3'] = 'pkdr_mqtt_port'
        pkdr_utils.config_dict['db_table_dict']['val3'] = variables_dict["pkdr_mqtt_port"]
        pkdr_utils.db_generic_insert()
    else:

        pkdr_mqtt_client.loop_start()  # start the loop

        try:
            # Subscribe to CHIME
            ret = pkdr_mqtt_client.subscribe(
                variables_dict["mqtt_subscribe_topic"],
                qos=variables_dict["mqtt_subscribe_qos"],
            )  # publish
            if variables_dict["verbosity"] > 1:
                runtime_messages += "INFO: Subscribe Topic: {} = ret({})\n".format(variables_dict["mqtt_subscribe_topic"], ret)
                runtime_messages += "INFO: Subscribe Topic: {} = ret({})\n".format(variables_dict["mqtt_subscribe_volume"], ret)
                print('K-VDB-Runtime: '.format(runtime_messages))

            while True:
                # pause the loop to give MQTT some time to receive a new message
                time.sleep(variables_dict["sleep_in_loop"])

        except KeyboardInterrupt:
            log_level = 4 # 4 = CRITICAL
            runtime_messages += "ERROR: CTRL-C pressed.  Program exiting..."
            runtime_error_flag = True
            pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
            pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
            pkdr_utils.config_dict['db_table_dict']['log_message'] = runtime_messages
            pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
            pkdr_utils.config_dict['db_table_dict']['val0'] = 'doorbell->exception->ctl_c'
            pkdr_utils.db_generic_insert()
            pkdr_mqtt_client.loop_stop()  # stop the loop

        pkdr_mqtt_client.loop_stop()  # stop the loop

        pkdr_mqtt_client.disconnect()

# -------------------------------------------
# ----- Program Execution Block - End -----
# -------------------------------------------


# Paho Python MQTT Client-Understanding The Loop
# http://www.steves-internet-guide.com/loop-python-mqtt-client/
# Because the loop is a blocking function I call it with a timeout the default timeout is 1 second.
# If you call the loop manually then you will need to create code to handle reconnects.
# Important! If your client script has more than one client connection then you must call or start a loop for each client connection.
# For example, if I create two clients client 1 and client2 in a script, then you would expect to see client1.loop() and client2.loop() in the script.

# http://www.steves-internet-guide.com/mqtt-python-callbacks/
# Loop example that disconnects when loop_flag_exit is not 1
# Note: the below comes after loop_start()
# loop_count = 0
# while variables_dict['loop_flag_exit'] == 1:
#     print("waiting for callback to occur {}", format(loop_count))
#     time.sleep(0.01) # pause 1/100 second
#     loop_count += 1

# Example of Queue and List processing
# while len(messages)>0:
#     print(messages.pop(0))
# while not msg_q.empty():
#     message = msg_q.get()
#     print("queue: {}".format(message))

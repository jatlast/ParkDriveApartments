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
# Code Formatting using black executed using windows shells (as of 20220226 requires revision)
#  black pkdr_kiosk_doorbell.py --target-version py39 --verbose --config FILE
# ------------

# /bin/sh -c /usr/bin/python3 /home/PkDr/HA/code/PROD/python/pkdr_i2c_to_db.py -v 0 >> /home/pi/pkdr/logs/i2c_to_db.log 2>> /home/pi/pkdr/logs/i2c_to_db.err
# python3 /home/PkDr/HA/code/DEV/python/pkdr_kiosk_relays.py -v 4 >> /home/pi/pkdr/logs/kiosk_relays.log 2>> /home/pi/pkdr/logs/kiosk_relays.err

# 20220227 - Tasmota MQTT naming conventions https://tasmota.github.io/docs/MQTT/
# FullTopic~
#     This is the MQTT topic used to communicate with Tasmota over MQTT. It is created using tokens placed within a user definable string (100 character limit). The tokens are substituted dynamically at run-time. Available substitution tokens are:
# %prefix% = one of three prefixes as defined by commands Prefix1 (default = cmnd), Prefix2 (default = stat) and Prefix3 (default = tele).
# %topic% = one of five topics as defined by commands Topic, GroupTopic, ButtonTopic, SwitchTopic and MqttClient.
# If FullTopic does not contain the %topic% token, the device will not subscribe to GroupTopic and FallbackTopic.
# Examples~
#     In the following examples %topic% is tasmota, FullTopic is %prefix%/%topic%/, and prefixes are default cmnd/stat/tele:
#     The relay can be controlled with cmnd/tasmota/POWER on, cmnd/tasmota/POWER off or cmnd/tasmota/POWER toggle. Tasmota will send a MQTT status message like stat/tasmota/POWER ON.
# While most MQTT commands will result in a message in JSON format the power status feedback will always be returned like stat/tasmota/POWER ON as well.
#     Telemetry data will be sent by prefix tele like tele/tasmota/SENSOR {"Time":"2017-02-16T10:13:52", "DS18B20":{"Temperature":20.6}}
# %prefix%~
#     Tasmota uses 3 prefixes for forming a FullTopic:
#         cmnd - prefix to issue commands; ask for status
#         stat - reports back status or configuration message
#         tele - reports telemetry info at specified intervals

# Example using PkDr AC Outlet as currently configured by JTB:
#   %topic% = AC
#   FullTopic = PkDr/Apt01/LivingRoom/%prefix%/%topic%/
#   Tasmota Notea:
#       The order of %prefix% and %topic% doesn't matter, unless you have enabled Auto-discovery for Home Assistant (SetOption19). Enabling this option re-formats the FullTopic to required order.
#       Using the tokens the following example topics can be made:
#           FullTopic %prefix%/%topic%/ default
#           FullTopic tasmota/%topic%/%prefix%/
#           FullTopic tasmota/bedroom/%topic%/%prefix%/
#           FullTopic penthouse/bedroom1/bathroom2/%topic%/%prefix%/
#           FullTopic %prefix%/home/cellar/%topic%/
# ----- IMPORTANT 20220227 -----
# My config for all Tasmota devices needs to be change
# From...
#   FullTopic = PkDr/Apt01/LivingRoom/%prefix%/%topic%/
#   Example   = PkDr/Apt01/LivingRoom/cmnd/AC/
# To...
#   FullTopic = PkDr/Apt01/LivingRoom/%topic%/%prefix%/
#   Example   = PkDr/Apt01/LivingRoom/AC/cmnd/
# ------------------------------

# Home Assistant - MQTT Discovery - https://www.home-assistant.io/docs/mqtt/discovery/
# DISCOVERY TOPIC
# The discovery topic needs to follow a specific format:
#   <discovery_prefix>/<component>/[<node_id>/]<object_id>/config
# Text
#   <component>: One of the supported MQTT components, eg. binary_sensor. (Note: supported components are listed on teh MQTT Discovery page - see above URL)
#   <node_id> (Optional): ID of the node providing the topic, this is not used by Home Assistant but may be used to structure the MQTT topic. The ID of the node must only consist of characters from the character class [a-zA-Z0-9_-] (alphanumerics, underscore and hyphen).
#   <object_id>: The ID of the device. This is only to allow for separate topics for each device and is not used for the entity_id. The ID of the device must only consist of characters from the character class [a-zA-Z0-9_-] (alphanumerics, underscore and hyphen).
# Current PkDr MQTT conventions and possible HA required substitutions...
#   Example      = PkDr/Apt01/LivingRoom/cmnd/AC/
#   HA variables = <discovery_prefix>/Apt01/LivingRoom/<component>/cmnd/<object_id>/
#   HA substitue = PkDr/Apt01/LivingRoom/switch/cmnd/apt01_ac/

# To-Do
#     1 - Update Tasmota Fulltopics across all PkDr Tasmota devices (see above)
#     2 - update all current HA "platform: mqtt" objects to have a "unique_id: " based on lowercased and underscored "name:" values. (VSCode note: "Ctrl + Shift + P" brings up menu then type "lowercase")
#     3 - Change temperature & humidity sensor from "sql" to "mqtt" - this will require...
#     https://www.home-assistant.io/integrations/sensor.mqtt/
#             - Python JSON https://docs.python.org/3/library/json.html

# For To-Do #3 - may not be relevant because it is a "light" not a "sensor" - I don't have any mqtt sensors yet ...
# Example Tasmota MQTT device from PkDr's configuration.yaml...
# ### Apt 01
#   # Entrance
#   - platform: mqtt
#     name: "Apt01 Entrance Bulb"
#     command_topic: "PkDr/Apt01/Entrance/cmnd/Bulb/POWER"
#     state_topic: "PkDr/Apt01/Entrance/stat/Bulb/RESULT"
#     state_value_template: "{{value_json.POWER}}"
#     availability_topic: "PkDr/Apt01/Entrance/tele/Bulb/LWT"
#     brightness_command_topic: "PkDr/Apt01/Entrance/cmnd/Bulb/Dimmer"
#     brightness_state_topic: "PkDr/Apt01/Entrance/stat/Bulb/RESULT"
#     brightness_scale: 100
#     on_command_type: "brightness"
#     brightness_value_template: "{{value_json.Dimmer}}"
#     color_temp_command_topic: "PkDr/Apt01/Entrance/cmnd/Bulb/CT"
#     color_temp_state_topic: "PkDr/Apt01/Entrance/tele/Bulb/STATE"
#     color_temp_value_template: "{{value_json.CT}}"
#     rgb_command_topic: "PkDr/Apt01/Entrance/cmnd/Bulb/Color2"
#     rgb_state_topic: "PkDr/Apt01/Entrance/stat/Bulb/RESULT"
#     rgb_value_template: "{{value_json.Color.split(',')[0:3]|join(',')}}"
#     effect_command_topic: "PkDr/Apt01/Entrance/cmnd/Bulb/Scheme"
#     effect_state_topic: "PkDr/Apt01/Entrance/tele/Bulb/RESULT"
#     effect_value_template: "{{value_json.Scheme}}"
#     effect_list:
#       - 0 none
#       - 2 color cycle
#     payload_on: "ON"
#     payload_off: "OFF"
#     payload_available: "Online"
#     payload_not_available: "Offline"
#     qos: 1
# #    retain: false


import board
from digitalio import DigitalInOut, Direction
import time # needed to sleep the listening loop
import vlc # needed to play doorbell .wav file
import paho.mqtt.client as mqtt # needed to listen for MQTT messages
    # https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php
import datetime # needed for now()
import argparse # allow command line options
# import pkdr_utils # (JTB Script as Util) loads the local configurations for all PkDr Scripts
from pkdr_utils import utils as pkdr_utils

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

# The Quality of Service (QoS) level is an agreement between the sender of a message and the receiver of a message
#  that defines the guarantee of delivery for a specific message. There are 3 QoS levels in MQTT:
#     At most once (0)
#     At least once (1)
#     Exactly once (2)

variables_dict = {
    'program_name': parser.prog,
    'verbosity': args.verbosity,
    'sleep_in_loop': 0.50,
    'sleep_after_vlc': 10.00,  # allow time to play the full media file
    # The suscribe method accepts 2 parameters.  Note: can suscribe to more than one topic at a time.
    #    subscribe(topic, qos=0)
    'doorbell_volume': 60,  # 60 is the default volume setting
    'mqtt_subscribe_qos': 1, # QoS 1 - at least once
    'mqtt_publish_qos' : 1,  # QoS 1 - at least once
    'mqtt_publish_retain' : True,
    'topic_root' : 'PkDr',
    # 'topic_suffix' : 'Utility/output',
    'topic_suffix' : 'Utility',
    'command_topic_suffix' : 'set',
    # The message payload that triggers the action of this program
    'payload_for_switch': 'POWER',
    'payload_for_doorbell': 'CHIME',
    'sound_played': '',
    'action_previous_doorbell': datetime.datetime.now(),
}

log_level = 10 # Dummy Number
runtime_messages = ''
runtime_error_message = ''
runtime_error_flag = False
global_state_topics_dict = {}

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
    pkdr_utils.config_dict['db_table_dict']['val0'] = 'kiosk->config->error'

    if not pkdr_utils.config_dict['mqtt_valid'] or pkdr_utils.config_dict['sound_config_error_flag']:
        pkdr_utils.config_dict['db_table_dict']['log_message'] += pkdr_utils.config_dict['caller_error_msg']
    elif pkdr_utils.config_dict['mqtt_credentials_error_flag']:
        pkdr_utils.config_dict['db_table_dict']['log_message'] += pkdr_utils.config_dict['mqtt_credentials_error_msg']
 
    # log the error
    pkdr_utils.db_generic_insert()
else:
    # initialize the root of the log key...
    pkdr_utils.config_dict['db_table_dict']['val0'] = 'kiosk->'

    RELAY_CLOSED = False
    RELAY_OPEN   = not RELAY_CLOSED

    # the output of "dir(board)" on a Pi3 (likely true of all Pi models: zero through 4)...
    # ['CE0', 'CE1', 'D0', 'D1', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D19', 'D2', 'D20', 'D21', 'D22', 'D23', 'D24', 'D25', 'D26', 'D27', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'I2C', 'MISO', 'MISO_1', 'MOSI', 'MOSI_1', 'RX', 'RXD', 'SCK', 'SCK_1', 'SCL', 'SCLK', 'SCLK_1', 'SDA', 'SPI', 'TX', 'TXD', '__blinka__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__repo__', '__spec__', '__version__', 'ap_board', 'board_id', 'detector', 'pin', 'sys']

    # Zone Valve Transformer @ 40VA / 24V AC (Red & White)
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    # RELAY_01 @ board.D5     # Heat - 1, 5, 9, 13
    RELAY_01 = DigitalInOut(board.D5)
    RELAY_01.direction = Direction.OUTPUT
    # RELAY_02 @ board.D6     # Heat - 2, 6, 10, 14
    RELAY_02 = DigitalInOut(board.D6)
    RELAY_02.direction = Direction.OUTPUT
    # RELAY_03 @ board.D13    # Heat - 3, 7, 11, 15
    RELAY_03 = DigitalInOut(board.D13)
    RELAY_03.direction = Direction.OUTPUT
    # RELAY_04 @ board.D16    # Heat - 4, 8, 12, 16
    RELAY_04 = DigitalInOut(board.D16)
    RELAY_04.direction = Direction.OUTPUT

    # Kiosk Transformer @ 50VA / 24V AC (Orange & Black)
    # ------------- A & B ---------------
    # ---------- Normally Closed ----------
    # RELAY_05 @ board.D19    # Kiosks - 1 & 3, 5 & 7,  9 & 11, 13 & 15
    RELAY_05 = DigitalInOut(board.D19)
    RELAY_05.direction = Direction.OUTPUT
    # RELAY_06 @ board.D20    # Kiosks - 2 & 4, 6 & 8, 10 & 12, 14 & 16
    RELAY_06 = DigitalInOut(board.D20)
    RELAY_06.direction = Direction.OUTPUT
    # RELAY_07 @ board.D21    # Entrance Pi Button Monitor - B1, B2, B3, B4
    RELAY_07 = DigitalInOut(board.D21)
    RELAY_07.direction = Direction.OUTPUT
    # RELAY_08 @ board.D26    # Entrance TTGo VDB - B1, B2, B3, B4
    RELAY_08 = DigitalInOut(board.D26)
    RELAY_08.direction = Direction.OUTPUT

    # Second bank of eight relays (10-wire harness connected to auxiliar GPIO header)
    # (colors from the black side down)

    # Locks Transformer @ 24VA / 12V DC (Green & Blue)
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    # white
    # RELAY_16 @ board.D23    # Apt Locks - 1, 5,  9, 13
    RELAY_16 = DigitalInOut(board.D23)
    RELAY_16.direction = Direction.OUTPUT
    # green
    # RELAY_15 @ board.D18    # Apt Locks - 2, 6, 10, 14
    RELAY_15 = DigitalInOut(board.D18)
    RELAY_15.direction = Direction.OUTPUT
    # yellow
    # RELAY_14 @ board.D15    # Apt Locks - 3, 7, 11, 15
    RELAY_14 = DigitalInOut(board.D15)
    RELAY_14.direction = Direction.OUTPUT
    # blue
    # RELAY_13 @ board.D14    # Apt Locks - 4, 8, 12, 16
    RELAY_13 = DigitalInOut(board.D14)
    RELAY_13.direction = Direction.OUTPUT
    # yellow
    # RELAY_12 @ board.D22    # Building Entrance Locks - B1, B2, B3, B4
    RELAY_12 = DigitalInOut(board.D22)
    RELAY_12.direction = Direction.OUTPUT

    # VDb-R Transformer @ 30VA / 16V AC (Yellow & Brown)
    # ------------- A & B ---------------
    # ---------- Normally Closed ----------
    # green
    # RELAY_11 @ board.D27    # Apt VDBs - 1 & 3, 5 & 7,  9 & 11, 13 & 15
    RELAY_11 = DigitalInOut(board.D27)
    RELAY_11.direction = Direction.OUTPUT
    # blue
    # RELAY_10 @ board.D17    # Apt VDBs - 2 & 4, 6 & 8, 10 & 12, 14 & 16
    RELAY_10 = DigitalInOut(board.D17)
    RELAY_10.direction = Direction.OUTPUT

    # --- No Transformer ---
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    # red & white
    # RELAY_09 @ board.D4     # End Switdh Override
    RELAY_09 = DigitalInOut(board.D4)
    RELAY_09.direction = Direction.OUTPUT

    # DigitalInOut object dict...
    digital_io_object_dict = {
    # First bank of eight relays (direct connection to GPIO header)

        # Zone Valve Transformer @ 40VA / 24V AC (Red & White)
        # ------------- A & C ---------------
        # ---------- Normally Open ----------
        'relay_01': RELAY_01      # Heat - 1, 5, 9, 13
        , 'relay_02': RELAY_02    # Heat - 2, 6, 10, 14
        , 'relay_03': RELAY_03    # Heat - 3, 7, 11, 15
        , 'relay_04': RELAY_04    # Heat - 4, 8, 12, 16

        # Kiosk Transformer @ 50VA / 24V AC (Orange & Black)
        # ------------- A & B ---------------
        # ---------- Normally Closed ----------
        , 'relay_05': RELAY_05    # Kiosks - 1 & 3, 5 & 7,  9 & 11, 13 & 15
        , 'relay_06': RELAY_06    # Kiosks - 2 & 4, 6 & 8, 10 & 12, 14 & 16
        , 'relay_07': RELAY_07    # Entrance Pi Button Monitor - B1, B2, B3, B4
        , 'relay_08': RELAY_08    # Entrance TTGo VDB - B1, B2, B3, B4

    # Second bank of eight relays (10-wire harness connected to auxiliar GPIO header)
        # (colors from the black side down)

        # Locks Transformer @ 24VA / 12V DC (Green & Blue)
        # ------------- A & C ---------------
        # ---------- Normally Open ----------
        # white
        , 'relay_16': RELAY_16    # Apt Locks - 1, 5,  9, 13
        # green
        , 'relay_15': RELAY_15    # Apt Locks - 2, 6, 10, 14
        # yellow
        , 'relay_14': RELAY_14    # Apt Locks - 3, 7, 11, 15
        # blue
        , 'relay_13': RELAY_13    # Apt Locks - 4, 8, 12, 16
        # yellow
        , 'relay_12': RELAY_12    # Building Entrance Locks - B1, B2, B3, B4

        # VDb-R Transformer @ 30VA / 16V AC (Yellow & Brown)
        # ------------- A & B ---------------
        # ---------- Normally Closed ----------
        # green
        , 'relay_11': RELAY_11    # Apt VDBs - 1 & 3, 5 & 7,  9 & 11, 13 & 15
        # blue
        , 'relay_10': RELAY_10    # Apt VDBs - 2 & 4, 6 & 8, 10 & 12, 14 & 16

        # --- No Transformer ---
        # ------------- A & C ---------------
        # ---------- Normally Open ----------
        # red & white
        , 'relay_09': RELAY_09     # End Switdh Override
    }
    # initialize all to open
    count = 0
    for i in digital_io_object_dict:
        if variables_dict['verbosity'] > 3:
            print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
        digital_io_object_dict[i].value = RELAY_OPEN
        count += 1

    # -----------------------------------------
    # ----- Relay Functions - Start -----------
    # -----------------------------------------
    def relay_test_all(relay_dict):
        print('relay_test_all()')
        count = 0
        # set all to open rapidly...
        for i in digital_io_object_dict:
            if variables_dict['verbosity'] > 3:
                print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
            digital_io_object_dict[i].value = RELAY_OPEN
            count += 1
        count = 0
        # close one by one slowly...
        for i in relay_dict:
            if variables_dict['verbosity'] > 3:
                print("{} | Set {} GPIO {} to ON by sending {}".format(count, i, relay_dict[i], RELAY_CLOSED))
            relay_dict[i].value = RELAY_CLOSED
            time.sleep(0.5)
            count += 1
        count = 0
        # reset all to open rapidly...
        for i in digital_io_object_dict:
            if variables_dict['verbosity'] > 3:
                print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
            digital_io_object_dict[i].value = RELAY_OPEN
            count += 1
    
    # relay_test_all(digital_io_object_dict)
    # -----------------------------------------
    # ----- Relay Functions - End -------------
    # -----------------------------------------

    # --------------------------------------------
    # ----- Doorbell Functions - Start -----------
    # --------------------------------------------
    def doorbell_ring_local_usb():
        action_current_datetime = datetime.datetime.now()
        action_duration = (action_current_datetime - variables_dict['action_previous_doorbell'])
        # reset the previous action variable
        variables_dict['action_previous_doorbell'] = action_current_datetime
        variables_dict['sound_1'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_main']
        variables_dict['sound_2'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
        variables_dict['sound_3'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_2']
        variables_dict['sound_4'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
        variables_dict['sound_patience'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['system_start']

        # Duration in seconds
        seconds = action_duration.total_seconds()
        # Duration in years
        years = divmod(seconds, 31536000)[0]  # Seconds in a year=365*24*60*60 = 31536000.
        # Duration in days
        days = action_duration.days  # Built-in datetime function
        # days = divmod(seconds, 86400)[0]       # Seconds in a day = 86400
        # Duration in hours
        hours = divmod(seconds, 3600)[0]  # Seconds in an hour = 3600
        # Duration in minutes
        minutes = divmod(seconds, 60)[0]  # Seconds in a minute = 60

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
            print("{}: K-VDB-Runtime: Found: {} | Played: {} | Previous: {}".format(datetime.datetime.now(), variables_dict['payload_for_doorbell'], variables_dict['sound_played'], duration_since_last_doorbell))
    # --------------------------------------------
    # ----- Doorbell Functions - End -------------
    # --------------------------------------------

    def get_mqtt_state_topics():
        # Example topics...
        #   state_topic: PkDr/B4/Utility/13_Heat
        #   command_topic: PkDr/B4/Utility/13_Heat/set

        # cmd_topic PkDr/B4/Utility/13_heat/set != message.topic PkDr/B4/Utility/output/13_Heat
        # cmd_topic PkDr/B4/Utility/output/16_Lock/set != message.topic PkDr/B4/Utility/output/16_Heat/set
        # cmd_topic PkDr/B4/Utility/output/B4_Kiosks_Even/set != message.topic PkDr/B4/Utility/output/Kiosks_Even/set

        state_topics_dict = {}

        # cycle through the relays and match topics to relays...
        count = 0
        mqtt_config_error_flag = False
        if pkdr_utils.config_dict['pkdr_mqtt_config']['pkdr_id_to_mqtt_dict'].get(pkdr_utils.config_dict['pkdr_location_id'], -1) == -1:
            mqtt_config_error_flag = True
            print('{}: Error->MQTT->Config->ID: pkdr_id_to_mqtt_dict[{}] not found'.format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['pkdr_location_id']))
        else:
            for key in digital_io_object_dict.keys():
                # check if relay is configured for the current running environment...
                found_value = pkdr_utils.config_dict['pkdr_mqtt_config']['pkdr_id_to_mqtt_dict'][pkdr_utils.config_dict['pkdr_location_id']].get(key, -1)
                if found_value == -1:
                    mqtt_config_error_flag = True
                    print('{}: Error->MQTT->Config->ID->Relay#: pkdr_id_to_mqtt_dict[{}][{}] not found | count = {}'.format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['pkdr_location_id'], key, count))
                    break
                else:
                    state_topics_dict[key] = '{}/{}/{}/{}'.format(variables_dict['topic_root'], pkdr_utils.config_dict['pkdr_location_id'], variables_dict['topic_suffix'], found_value)
                    if pkdr_utils.config_dict['verbosity'] > 2:
                        print('{}: Found: pkdr_id_to_mqtt_dict[{}][{}] | count = {} | {} subscribes to topic {}'.format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['pkdr_location_id'], key, count, key, state_topics_dict[key]))
                count += 1

        if(mqtt_config_error_flag and pkdr_utils.config_dict['verbosity'] > 0):
            print('{}: ERROR: get_mqtt_state_topics() failed | count = {}'.format(pkdr_utils.config_dict['datestamp'], count))

        return state_topics_dict


    # -------------------------------------------
    # ----- Calback Functions - Start -----------
    # -------------------------------------------
    def on_subscribe(client, userdata, mid, granted_qos):
        if variables_dict['verbosity'] > 2:
            print('{}: on_subscribe(client={}, userdata={}, mid={}, granted_qos={})'.format(datetime.datetime.now(), client, userdata, mid, granted_qos))

    def on_publish(client, userdata, result):
        if variables_dict['verbosity'] > 2:
            print('{}: on_publish(client={}, userdata={}, result={})'.format(datetime.datetime.now(), client, userdata, result))

    def on_disconnect(client, userdata, rc):
        if variables_dict['verbosity'] > 2:
            print('{}: on_disconnect(client={}, userdata={}, rc={})'.format(client, userdata, rc))
        client.loop_stop()

    # Note the message parameter is a message class with members: topic, qos, payload, retain.
    def on_message(client, userdata, message):
        global global_state_topics_dict
        payload_relevant_flag = False
        payload_captured_flag = False
        payload_change_state_flag = False
        payload_published_flag = False
        action_current_datetime = datetime.datetime.now()
        if variables_dict['verbosity'] > 3:
            print("{} INFO: on_message() - Topic: {} | Payload: {}\n".format(action_current_datetime, message.topic, str(message.payload.decode('utf-8'))))

        count = 0
        relay_used = ''
        for cmd_relay, state_topic in global_state_topics_dict.items():
            count += 1
            cmd_topic = '{}/{}'.format(state_topic, variables_dict['command_topic_suffix'])
            if cmd_topic == message.topic:
                payload_relevant_flag = True
                if digital_io_object_dict.get(cmd_relay, -1) == -1:
                    if variables_dict['verbosity'] > 3:
                        print('{} Config Error: digital_io_object_dict[{}] not found | count = {}'.format(pkdr_utils.config_dict['datestamp'], cmd_relay, count))
                else:
                    print("{} - change to {}".format(cmd_relay, str(message.payload.decode('utf-8'))))
                    if(str(message.payload.decode('utf-8')) == 'ON' or str(message.payload.decode('utf-8')) == 'OFF'):
                        relay_used = cmd_relay
                        if(str(message.payload.decode('utf-8')) == 'ON'):
                            payload_captured_flag = True
                            if digital_io_object_dict[cmd_relay].value != RELAY_CLOSED:
                                payload_change_state_flag = True
                                if variables_dict['verbosity'] > 3:
                                    print('{}.value = RELAY_CLOSED | Payload {}'.format(cmd_relay, str(message.payload.decode('utf-8'))))
                                digital_io_object_dict[cmd_relay].value = RELAY_CLOSED
                            else:
                                if variables_dict['verbosity'] > 3:
                                    print('{}.value already RELAY_CLOSED'.format(cmd_relay))
                        elif(str(message.payload.decode('utf-8')) == 'OFF'):
                            payload_captured_flag = True
                            if digital_io_object_dict[cmd_relay].value != RELAY_OPEN:
                                payload_change_state_flag = True
                                if variables_dict['verbosity'] > 3:
                                    print('{}.value = RELAY_OPEN | Payload {}'.format(cmd_relay, str(message.payload.decode('utf-8'))))
                                digital_io_object_dict[cmd_relay].value = RELAY_OPEN
                            else:
                                if variables_dict['verbosity'] > 3:
                                    print('{}.value already RELAY_OPEN'.format(cmd_relay))

                        # publish acknowleged state...
                        ret = pkdr_mqtt_client.publish(state_topic, payload=str(message.payload.decode('utf-8')), qos=variables_dict['mqtt_publish_qos'], retain=variables_dict['mqtt_publish_retain'])
                        if ret[0] != mqtt.MQTT_ERR_SUCCESS:
                            if variables_dict['verbosity'] > 0:
                                print('{} ERROR MQTT: publish(topic={}, payload={}, qos={}, retain={}) return={} != mqtt.success={}'.format(action_current_datetime, state_topic, str(message.payload.decode('utf-8')), variables_dict['mqtt_publish_qos'], variables_dict['mqtt_publish_retain'], str(ret), str(mqtt.MQTT_ERR_SUCCESS)))
                        else:
                            payload_published_flag = True
                            if variables_dict['verbosity'] > 3:
                                print('{} SUCCESS MQTT: publish(topic={}, payload={}, qos={}, retain={}) return={}'.format(action_current_datetime, state_topic, str(message.payload.decode('utf-8')), variables_dict['mqtt_publish_qos'], variables_dict['mqtt_publish_retain'], str(ret)))
                    else:
                        if variables_dict['verbosity'] > 2:
                            print('payload {} != (ON | OFF)'.format(str(message.payload.decode('utf-8'))))
                break
            else:
                if variables_dict['verbosity'] > 3:
                    print('cmd_topic {} != message.topic {}'.format(cmd_topic, message.topic))
                # after the message topic has been matched with an item from teh topics_dict: publish the change, set the db variables, and exit the loop
        
        if payload_change_state_flag:
            # re-init the db_table_dict to flush all the db variable key/val pairs...
            pkdr_utils.db_table_dict_init_force()

            pkdr_utils.db_variables_add_key_value('payload', str(message.payload.decode('utf-8')))
            pkdr_utils.db_variables_add_key_value('topic', message.topic)
            pkdr_utils.db_variables_add_key_value('relay', relay_used)

            # add a db variable detailing the result of this relevant on_message()
            flag_key_val = 'kiosk->payload->captured'
            if not payload_published_flag:
                flag_key_val += '->not->published'
            else:
                flag_key_val += '->published'

            pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
            pkdr_utils.config_dict['db_table_dict']['val0'] = flag_key_val

            # Log the doorbell ring...
            msg_log_level = 1 # INFO
            pkdr_utils.config_dict['db_table_dict']['log_level'] = msg_log_level
            pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][msg_log_level]
            pkdr_utils.config_dict['db_table_dict']['log_message'] = 'MQTT Message Relevant'
            
            pkdr_utils.db_generic_insert()
        else:
            if variables_dict['verbosity'] > 3:
                print('{}: Payload Flags: relevant={} | captured={} | change_state={} | published={}'.format(action_current_datetime, payload_relevant_flag, payload_captured_flag, payload_change_state_flag, payload_published_flag))

    def on_log(client, userdata, level, buf):
        paho_log_level_name = pkdr_utils.config_dict['pkdr_mqtt_config']['paho_client_dict']['log_levels_dict'].get(level, 'Lookup failed for level=({})'.format(level))
        log_if = pkdr_utils.config_dict['pkdr_mqtt_config']['paho_client_dict']['log_levels_if_dict'].get(paho_log_level_name, False)

        if log_if:
            log_level = 1 # 1 = INFO
            pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
            pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
            pkdr_utils.config_dict['db_table_dict']['log_message'] = 'MQTT Runtime Log'
            pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'mqtt->on_log'

            pkdr_utils.db_variables_add_key_value('log_if', log_if)
            pkdr_utils.db_variables_add_key_value('level_lookup', paho_log_level_name)
            pkdr_utils.db_variables_add_key_value('level', level)
            pkdr_utils.db_variables_add_key_value('mqtt_callback', 'def on_log(client, userdata, level, buf)')
            pkdr_utils.db_variables_add_key_value('buf', buf)

            pkdr_utils.db_generic_insert()
            if variables_dict['verbosity'] > 1:
                print('{}: K-VDB-Runtime: {}'.format(datetime.datetime.now(), pkdr_utils.config_dict['db_table_dict']['log_message']))
        else:
            if variables_dict['verbosity'] > 2:
                print('{}: Not Logged: {}->{} log->{}'.format(datetime.datetime.now(), level, paho_log_level_name, log_if))

    # -------------------------------------------
    # ----- Calback Functions - End -------------
    # -------------------------------------------

    # -------------------------------------------
    # ----- Program Execution Block - Start -----
    # -------------------------------------------
    variables_dict['pkdr_mqtt_ip'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_broker_ip', 'KeyError')
    variables_dict['pkdr_mqtt_port'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_broker_port', 'KeyError')
    variables_dict['pkdr_mqtt_un'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_username', 'KeyError')
    variables_dict['pkdr_mqtt_pw'] = pkdr_utils.config_dict['pkdr_mqtt_config']['mosquitto_broker_config']['credentials_dict'].get('pkdr_mqtt_password', 'KeyError')

    # Building Kiosks subscribe to all relevant topics by subscribing to the root of their topic...
    variables_dict['kiosk_mqtt_topic_subscribe'] = '{}/{}/{}/#'.format(variables_dict['topic_root'], pkdr_utils.config_dict['pkdr_location_id'], variables_dict['topic_suffix'])

    variables_dict['pkdr_mqtt_client'] = pkdr_utils.config_dict['pkdr_location_id']

    global_state_topics_dict = get_mqtt_state_topics()

    if variables_dict['verbosity'] > 0:
        print('{}: K-VDB-Runtime: {}'.format(datetime.datetime.now(), runtime_messages))

    pkdr_mqtt_client = mqtt.Client(variables_dict['pkdr_mqtt_client'])  # create client object

    # bind to the mqtt callback function...
    pkdr_mqtt_client.on_publish = on_subscribe
    pkdr_mqtt_client.on_publish = on_publish
    pkdr_mqtt_client.on_message = on_message
    pkdr_mqtt_client.on_log = on_log

    # print("mqtt user ({}) pw ({})".format(variables_dict['pkdr_mqtt_un'], variables_dict['pkdr_mqtt_pw']))
    pkdr_mqtt_client.username_pw_set(username=variables_dict['pkdr_mqtt_un'],password=variables_dict['pkdr_mqtt_pw'])

    exception_msg = ''
    exception_type = ''
    exception_flag = False
    try:
        # 20220220 - try to connect
        # connect(host, port=1883, keepalive=60, bind_address="")
        pkdr_mqtt_client.connect(variables_dict['pkdr_mqtt_ip'], variables_dict['pkdr_mqtt_port'])  # establish connection
    except OSError as err:
        exception_type = '{}'.format(type(err))
        exception_msg = 'Exception pkdr_mqtt_client.connect(host={}, port={}) raised: OSError {}'.format(variables_dict['pkdr_mqtt_ip'], variables_dict['pkdr_mqtt_port'], err)
        exception_flag = True
    except BaseException as err:
        exception_type = '{}'.format(type(err))
        exception_msg = 'Exception pkdr_mqtt_client.connect(host={}, port={}) raised: Unexptected ({})|({})'.format(variables_dict['pkdr_mqtt_ip'], variables_dict['pkdr_mqtt_port'], type(err), err)
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
        pkdr_utils.config_dict['db_table_dict']['val0'] += 'exception'

        pkdr_utils.db_variables_add_key_value('pkdr_mqtt_ip', variables_dict['pkdr_mqtt_ip'])
        pkdr_utils.db_variables_add_key_value('pkdr_mqtt_port', variables_dict['pkdr_mqtt_port'])

        pkdr_utils.db_generic_insert()
    else:
        pkdr_mqtt_client.loop_start()  # start the loop
        try:
            # The function returns a tuple (result, mid), 
            # where result is MQTT_ERR_SUCCESS to indicate success or (MQTT_ERR_NO_CONN, None) if the client is not currently connected. 
            # mid is the message ID for the subscribe request. 
            # The mid value can be used to track the subscribe request by checking against the mid argument in the on_subscribe() callback if it is defined.
            # paho mqtt code on github: https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py
            ret = pkdr_mqtt_client.subscribe(variables_dict['kiosk_mqtt_topic_subscribe'], variables_dict['mqtt_subscribe_qos'])
            if ret[0] != mqtt.MQTT_ERR_SUCCESS:
                print('{} ERROR MQTT: subscribe(topic={}, qos={}) ret={}'.format(datetime.datetime.now(), variables_dict['kiosk_mqtt_topic_subscribe'], variables_dict['mqtt_subscribe_qos'], str(ret)))
            else:
                if variables_dict['verbosity'] > 2:
                    print('{} SUCCESS MQTT: subscribe(topic={}, qos={}) ret={}'.format(datetime.datetime.now(), variables_dict['kiosk_mqtt_topic_subscribe'], variables_dict['mqtt_subscribe_qos'], str(ret)))
                while True:
                    # pause the loop to give MQTT some time to receive a new message
                    time.sleep(variables_dict['sleep_in_loop'])

        # except KeyboardInterrupt:
        except BaseException as err:
            # runtime_messages += "ERROR: CTRL-C pressed.  Program exiting..."
            # runtime_error_flag = True
            log_level = 4 # 4 = CRITICAL
            pkdr_utils.config_dict['db_table_dict']['log_level'] = log_level
            pkdr_utils.config_dict['db_table_dict']['log_level_name'] = pkdr_utils.config_dict['pkdr_remote_db_config']['log_table_config_dict']['log_error_num_to_name_dict'][log_level] # 4 = CRITICAL
            pkdr_utils.config_dict['db_table_dict']['exception_type'] = '{}'.format(type(err))
            pkdr_utils.config_dict['db_table_dict']['exception_text'] = 'Exception pkdr_mqtt_client.subscribe(topic={}, qos={}) raised: Unexptected ({})|({})'.format(variables_dict['kiosk_mqtt_topic_subscribe'], variables_dict['mqtt_subscribe_qos'], type(err), err)
            pkdr_utils.config_dict['db_table_dict']['key0'] = 'log_key'
            pkdr_utils.config_dict['db_table_dict']['val0'] += 'exception->ctl_c'
            # pkdr_utils.config_dict['db_table_dict']['val0'] = 'kiosk->exception'
            pkdr_utils.db_generic_insert()
            # pkdr_mqtt_client.loop_stop()  # stop the loop

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

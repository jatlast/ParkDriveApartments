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
import datetime # needed for now()
import argparse # allow command line options

import pkdr_utils # (JTB Script as Util) loads the local configurations for all PkDr Scripts

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
    "doorbell_volume": 6,  # 6 is the default volume setting
    "mqtt_subscribe_qos": 1,
    # The message payload that triggers the action of this program
    "actionable_payload": "CHIME",
    "sound_played": "",
    "action_previous_datetime": datetime.datetime.now(),
}
# ----- Initialize using PkDr Utils -----
if not pkdr_utils.initialize_config_dict(variables_dict):
    print("{}: Configuration Failure ({})".format(pkdr_utils.config_dict['datestamp'], pkdr_utils.config_dict['error_msg']))
# ---------------------------------------
elif pkdr_utils.config_dict['sound_config_error_flag']:
    pkdr_utils.config_dict['db_table_dict']['msgtxt'] = 'Caller Config Error: '
    pkdr_utils.config_dict['db_table_dict']['msgtxt'] += pkdr_utils.config_dict['caller_error_msg']
    pkdr_utils.db_generic_insert('ErrorLog')
else:
    variables_dict['pkdr_mqtt_ip'] = pkdr_utils.config_dict['mqtt_broker_ip']
    variables_dict['pkdr_mqtt_port'] = pkdr_utils.config_dict['mqtt_broker_port']
    variables_dict['pkdr_mqtt_un'] = pkdr_utils.config_dict['mqtt_username']
    variables_dict['pkdr_mqtt_pw'] = pkdr_utils.config_dict['mqtt_password']
    variables_dict['pkdr_mqtt_client'] = pkdr_utils.config_dict['mqtt_client_id_kiosk_doorbell']
    variables_dict['sound_1'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_main']
    variables_dict['sound_2'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
    variables_dict['sound_3'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_2']
    variables_dict['sound_4'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['doorbell_alt_1']
    variables_dict['sound_patience'] = pkdr_utils.config_dict['sound_config']['sound_path'] + pkdr_utils.config_dict['sound_config']['sound_files_dict']['system_start']

    if pkdr_utils.config_dict['mqtt_valid']:
        variables_dict["mqtt_subscribe_topic"] = ("PkDr/" + pkdr_utils.config_dict['mqtt'] + "/Entrance/cmnd/Doorbell/POWER")
        variables_dict["mqtt_subscribe_volume"] = ("PkDr/" + pkdr_utils.config_dict['mqtt'] + "/Doorbell/stat/Volume/setVolume")
        variables_dict["pkdr_mqtt_client"] += "-" + pkdr_utils.config_dict['mqtt']

        if variables_dict["verbosity"] > 0:
            print("Topic Location: ({})".format(pkdr_utils.config_dict['mqtt']))
            print("MQQT Doorbell Topic: ({})".format(variables_dict["mqtt_subscribe_topic"],))
            print("MQQT Volume Topic: ({})".format(variables_dict["mqtt_subscribe_volume"],))

        def on_disconnect(client, userdata, rc):
            if variables_dict["verbosity"] > 2:
                print("client disconnected ok (rc = [{}])".format(rc))
            # logging.debug("DisConnected result code " + str(rc))
            client.loop_stop()

        # Note the message parameter is a message class with members: topic, qos, payload, retain.
        def on_message(client, userdata, message):
            # check the volume first...
            if message.topic == variables_dict["mqtt_subscribe_volume"]:
                print("doorbell_volume changed from {} to {}".format(variables_dict["doorbell_volume"]))
                variables_dict["doorbell_volume"] = str(message.payload.decode("utf-8"))
                print("{} Topic: {} | Payload: {}".format(datetime.datetime.now(),message.topic))

            if (str(message.payload.decode("utf-8")) == variables_dict["actionable_payload"]):

                action_current_datetime = datetime.datetime.now()
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
                    variables_dict["sound_played"] = variables_dict["sound_1"]
                elif seconds > 30:
                    variables_dict["sound_played"] = variables_dict["sound_2"]
                elif seconds > 20:
                    variables_dict["sound_played"] = variables_dict["sound_3"]
                elif seconds > variables_dict["sleep_after_vlc"]:
                    variables_dict["sound_played"] = variables_dict["sound_4"]
                else:
                    variables_dict["sound_played"] = variables_dict["sound_patience"]

                vlc_player = vlc.MediaPlayer(variables_dict["sound_played"])
                # https://www.geeksforgeeks.org/python-vlc-mediaplayer-setting-volume/
                vlc_player.audio_set_volume(variables_dict["doorbell_volume"])
                vlc_player.play()
                time.sleep(variables_dict["sleep_after_vlc"])

                # the stop() is required to prevent orphaned vlc player objects
                vlc_player.stop()

                if variables_dict["verbosity"] > 0:
                    print("Duration: seconds {} | minutes {} | hours {} | days {} | years {} | ".format(seconds, minutes, hours, days, years))
                    print(
                        "{} | Found: {} | Payload: {} | Topic: {} | Played: {}".format(
                            datetime.datetime.now(),
                            variables_dict["actionable_payload"],
                            str(message.payload.decode("utf-8")),
                            message.topic,
                            variables_dict["sound_played"],
                        ),
                        
                    )

        #        pkdr_mqtt_client.publish(variables_dict['mqtt_subscribe_topic'], payload=variables_dict['actionable_payload_reset'], qos=variables_dict['mqtt_publish_qos'], retain=variables_dict['mqtt_publish_retain'])
        #        time.sleep(variables_dict['loop_sleep'])

        def on_log(client, userdata, level, buf):
            if variables_dict["pkdr_mqtt_client"] > 1:
                print("log {}: {} {} {}".format(client, userdata, level, buf))

        pkdr_mqtt_client = mqtt.Client(variables_dict["pkdr_mqtt_client"])  # create client object

        # bind to the on_message function because this is where this script logic lives
        pkdr_mqtt_client.on_message = on_message

        if variables_dict["verbosity"] > 1:
            pkdr_mqtt_client.on_log = on_log

    #    print("mqtt user ({}) pw ({})".format(variables_dict["pkdr_mqtt_un"], variables_dict["pkdr_mqtt_pw"]))
        pkdr_mqtt_client.username_pw_set(username=variables_dict["pkdr_mqtt_un"],password=variables_dict["pkdr_mqtt_pw"])
        pkdr_mqtt_client.connect(variables_dict["pkdr_mqtt_ip"], variables_dict["pkdr_mqtt_port"])  # establish connection

        pkdr_mqtt_client.loop_start()  # start the loop

        try:
            # Subscribe to CHIME
            ret = pkdr_mqtt_client.subscribe(
                variables_dict["mqtt_subscribe_topic"],
                qos=variables_dict["mqtt_subscribe_qos"],
            )  # publish
            if variables_dict["verbosity"] > 1:
                print("Subscribe Topic: {} = ret({})".format(variables_dict["mqtt_subscribe_topic"], ret))
                print("Subscribe Topic: {} = ret({})".format(variables_dict["mqtt_subscribe_volume"], ret))

            while True:
                # pause the loop to give MQTT some time to receive a new message
                time.sleep(variables_dict["sleep_in_loop"])

        except KeyboardInterrupt:
            pkdr_mqtt_client.loop_stop()  # stop the loop
            if variables_dict["verbosity"] > 0:
                print("\nCTRL-C pressed.  Program exiting...Exited",)

        pkdr_mqtt_client.loop_stop()  # stop the loop

        pkdr_mqtt_client.disconnect()
    else:
        if variables_dict["verbosity"] >= 0:
            print("{}: Config Error: MQTT ({}) & Valid = ({})".format(pkdr_utils.config_dict["datestamp"], pkdr_utils.config_dict["mqtt"], pkdr_utils.config_dict["mqtt_valid"]))

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

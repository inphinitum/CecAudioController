#!/usr/bin/env python2

# ctrl-receiver.py
#
# Copyright (C) 2016 Javier Martinez <javi@flamingalah.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MECHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# This file provides a Python script to control a device via HDMI-CEC based
# on events published via http
#
# Depends on libcec <https://github.com/Pulse-Eight/libcec>
#
# Author: Javier Martinez <javi@flamingalah.net>

from CecAudioController import ConfigOptions
from CecAudioController import DeviceController
import requests

# Global variables
controller = None
config     = None

# listen_for_events
#
# Listens on the given URL for events and dispatches the type of event
# to the right function for further processing.
def listen_for_events():
    while True:
        response = requests.get(config.REST_URL)

        if response.status_code == config.REST_SUCCESS_CODE:
            json_data = response.json()

            if config.EVENTS in json_data:
                for event in json_data[config.EVENTS]:
                    if config.PB_NOTIF in event.keys():
                        process_playback_event(event)

# processPlaybackEvent(event)
#
# Expected event structure: {"Notification": int}
#
def process_playback_event(event):
    n_type = event[config.PB_NOTIF]

    if n_type == config.PB_NOTIF_PLAY or n_type == config.PB_NOTIF_ACTIVE_DEVICE:
        controller.power_on()
    elif n_type == config.PB_NOTIF_STOP:
        controller.standby()
    elif n_type == config.PB_NOTIF_INACTIVE_DEVICE:
        controller.delayed_standby(5)
    elif n_type == config.PB_NOTIF_PAUSE:
        controller.delayed_standby(config.POWER_OFF_DELAY_MINS * 60)

if __name__ == '__main__':
    # Gather configuration options
    config = ConfigOptions()
    config.read_from_file()

    # Initialize CEC stuff and listen for events if OK
    controller = DeviceController()
    if controller.init_CEC():
        print("Initialization OK, listening for events on " + config.REST_URL)
        listen_for_events()
    else:
        print("Initialization NOK, quitting...")
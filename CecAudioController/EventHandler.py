# EventHandler.py
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

import requests


class EventHandler:
    # Global variables
    _controller = None
    _config = None

    # __init__()
    #
    # Constructor
    def __init__(self, controller, config):
        self._controller = controller
        self._config = config

    # listen_for_events
    #
    # Listens on the given URL for events and dispatches the type of event
    # to the right function for further processing.
    def listen_for_events(self):
        while True:
            response = requests.get(self._config.REST_URL)

            if response.status_code == self._config.REST_SUCCESS_CODE:
                json_data = response.json()

                if self._config.EVENTS in json_data:
                    for event in json_data[self._config.EVENTS]:
                        if self._config.PB_NOTIF in event.keys():
                            self.process_playback_event(event)

    # processPlaybackEvent(event)
    #
    # Expected event structure: {"Notification": int}
    def process_playback_event(self, event):
        n_type = event[self._config.PB_NOTIF]

        if n_type == self._config.PB_NOTIF_PLAY or n_type == self._config.PB_NOTIF_ACTIVE_DEVICE:
            self._controller.power_on()
        elif n_type == self._config.PB_NOTIF_STOP:
            self._controller.standby()
        elif n_type == self._config.PB_NOTIF_INACTIVE_DEVICE:
            self._controller.delayed_standby(5)
        elif n_type == self._config.PB_NOTIF_PAUSE:
            self._controller.delayed_standby(self._config.POWER_OFF_DELAY_MINS * 60)

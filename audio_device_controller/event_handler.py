"""
Copyright 2016 Javier Martinez <javi@flamingalah.net>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import requests
import sys


class EventError(Exception):
    """Exception class for event handling errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


class EventHandler:
    """
    Handler of events. Can listen to an REST endpoint, process the received events
    and invoke the appropriate commands on a CecController object
    """

    def __init__(self, controller, config):
        """
        Constructor.

        :param controller: DeviceController to be used to call commands.
        :param config: ConfigOptions holding info on how json events are formed etc.
        :return: None
        """

        self._controller = controller
        self._config = config

    def listen_for_events(self):
        """
        Listens on the given URL for events and dispatches the type of event
        to the right function for further processing.

        Processes one response at a time. If you want to listen indefinitely you
        must loop outside.

        :return: None
        """

        response = requests.get(self._config.REST_URL)
        if response.status_code == self._config.REST_SUCCESS_CODE:
            try:
                self.process_json_response(response.json())
            except EventError as error:
                raise EventError("Response from " + self._config.REST_URL + error.message)
        else:
            raise EventError("Error: " + self._config.REST_URL +
                             " responded with status code: " + str(response.status_code))

    def process_json_response(self, json_data):
        """
        Parses the received json as specified in the config,
        and calls for further process in case of playback events.

        :param json_data: Received response in json format.
        :return: None
        """

        try:
            if self._config.EVENTS in json_data:
                for event in json_data[self._config.EVENTS]:
                    if self._config.PB_NOTIF in event.keys():
                        self._process_single_playback_event(event)
            else:
                raise EventError("Response malformed.")
        except TypeError:
            raise EventError("Response malformed.")

    def _process_single_playback_event(self, event):
        """
        Processes the given playback event and triggers the respective command. Expects the
        following structure: {str: int}.

        :param event: type of event to process
        :return: None
        """

        n_type = event[self._config.PB_NOTIF]

        if n_type == self._config.PB_NOTIF_PLAY or n_type == self._config.PB_NOTIF_ACTIVE_DEVICE:
            self._controller.power_on()
        elif n_type == self._config.PB_NOTIF_STOP:
            self._controller.standby()
        elif n_type == self._config.PB_NOTIF_INACTIVE_DEVICE:
            self._controller.delayed_standby(self._config.POWER_OFF_DELAY_MINS)     # Seconds in this case
        elif n_type == self._config.PB_NOTIF_PAUSE:
            self._controller.delayed_standby(self._config.POWER_OFF_DELAY_MINS * 60)
        else:
            sys.stdout.write("Type of playback event not recognised.")

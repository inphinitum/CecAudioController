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

    def __init__(self, session, config):
        """
        Constructor.

        :param session: SessionHandler to be used to call commands.
        :param config: ConfigOptions holding info on how json events are formed etc.
        :return: None
        """

        self._session = session
        self._config = config

    def listen_for_events(self):
        """
        Listens on the given URL for events and dispatches the type of event
        to the right function for further processing.

        Processes one response at a time. If you want to listen indefinitely you
        must loop outside.

        :return: None
        """
        import requests

        response = requests.get(self._config._REST_URL)
        if response.status_code is self._config._REST_SUCCESS_CODE:
            try:
                self.process_json_response(response.json())
            except EventError as error:
                raise EventError("Response from " + self._config._REST_URL + error.message)
        else:
            raise EventError("Error: " + self._config._REST_URL +
                             " responded with status code: " + str(response.status_code))

    def process_json_response(self, json_data):
        """
        Parses the received json as specified in the config,
        and calls for further process in case of playback events.

        :param json_data: Received response in json format.
        :return: None
        """

        try:
            if self._config._EVENTS in json_data:
                for event in json_data[self._config._EVENTS]:
                    if self._config._PB_NOTIF in event.keys():
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
        import sys

        n_type = event[self._config._PB_NOTIF]

        if n_type == self._config._PB_NOTIF_ACTIVE_DEVICE:
            self._session.active(True)
        elif n_type == self._config._PB_NOTIF_INACTIVE_DEVICE:
            self._session.active(False)
        elif n_type == self._config._PB_NOTIF_PLAY:
            self._session.play()
        elif n_type == self._config._PB_NOTIF_STOP or n_type == self._config._PB_NOTIF_PAUSE:
            self._session.pause(self._config._POWER_OFF_DELAY_MINS * 60)
        else:
            sys.stdout.write("Type of playback event not recognised.")


class ConfigOptions:
    """
    Handles configuration options, including reading from disk (config.ini)
    """

    def __init__(self):
        self.REST_URL                 = ""
        self.REST_SUCCESS_CODE        = 200  # Standard HTTP success response code
        self.EVENTS                   = ""
        self.PB_NOTIF                 = ""
        self.PB_NOTIF_STOP            = -1
        self.PB_NOTIF_PLAY            = -1
        self.PB_NOTIF_PAUSE           = -1
        self.PB_NOTIF_ACTIVE_DEVICE   = -1
        self.PB_NOTIF_INACTIVE_DEVICE = -1
        self.POWER_OFF_DELAY_MINS     = 10

    def read_from_file(self):
        """
        Reads from config.ini in the same directory the necessary configuration params.
        """
        import configparser

        config = configparser.ConfigParser()
        config.optionxform = str

        # Check that the parser could read one file, and then extract the data.
        if config.read("config.ini") == ["config.ini"]:
            # [EventServer]
            if config.has_option("EventServer", "rest_url"):
                self.REST_URL = config.get("EventServer", "rest_url")

            # [MediaFormat]
            if config.has_option("MediaFormat", "events"):
                self.EVENTS = config.get("MediaFormat", "events")
            if config.has_option("MediaFormat", "pb_notif"):
                self.PB_NOTIF = config.get("MediaFormat", "pb_notif")
            if config.has_option("MediaFormat", "pb_notif_stop"):
                self.PB_NOTIF_STOP = config.getint("MediaFormat", "pb_notif_stop")
            if config.has_option("MediaFormat", "pb_notif_play"):
                self.PB_NOTIF_PLAY = config.getint("MediaFormat", "pb_notif_play")
            if config.has_option("MediaFormat", "pb_notif_pause"):
                self.PB_NOTIF_PAUSE = config.getint("MediaFormat", "pb_notif_pause")
            if config.has_option("MediaFormat", "pb_notif_active_device"):
                self.PB_NOTIF_ACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_active_device")
            if config.has_option("MediaFormat", "pb_notif_inactive_device"):
                self.PB_NOTIF_INACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_inactive_device")

            # [DeviceControl]
            if config.has_option("DeviceControl", "power_off_delay_mins"):
                self.POWER_OFF_DELAY_MINS = config.getint("DeviceControl", "power_off_delay_mins")
        else:
            raise ValueError("Failed to open config.ini")

    def __str__(self):  # pragma: no cover
        """
        Returns a string with the current configuration.
        :return: str
        """

        ret = "Configuration options\n======================="
        ret += "\nURL:                 " + self.REST_URL
        ret += "\nEvents:              " + self.EVENTS
        ret += "\nPB notification:     " + self.PB_NOTIF
        ret += "\nPB stop:             " + str(self.PB_NOTIF_STOP)
        ret += "\nPB play:             " + str(self.PB_NOTIF_PLAY)
        ret += "\nPB pause:            " + str(self.PB_NOTIF_PAUSE)
        ret += "\nPB active device:    " + str(self.PB_NOTIF_ACTIVE_DEVICE)
        ret += "\nPB inactive device:  " + str(self.PB_NOTIF_INACTIVE_DEVICE)
        ret += "\nPB power off delay:  " + str(self.POWER_OFF_DELAY_MINS)
        return ret

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

import logging

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

        response = requests.get(self._config.rest_url)

        if response.status_code is self._config.rest_success_code:
            try:
                self.process_json_response(response.json())
            except EventError as error:
                raise EventError("Response from " + self._config.rest_url + error.message)
        else:
            raise EventError("Error: " + self._config.rest_url +
                             " responded with status code: " + str(response.status_code))

    def process_json_response(self, json_data):
        """
        Parses the received json as specified in the config,
        and calls for further process in case of playback events.

        :param json_data: Received response in json format.
        :return: None
        """

        logging.info("Event received: " + str(json_data))

        try:
            if self._config.events in json_data:
                for event in json_data[self._config.events]:
                    if self._config.pb_notif in event.keys():
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

        n_type = event[self._config.pb_notif]

        if n_type is self._config.pb_notif_active_device:
            self._session.active(True)
        elif n_type is self._config.pb_notif_inactive_device:
            self._session.active(False)
        elif n_type is self._config.pb_notif_play:
            self._session.play()
        elif n_type is self._config.pb_notif_stop or n_type is self._config.pb_notif_pause:
            self._session.pause(self._config.power_off_delay_mins * 60)
        else:
            logging.warning("Type of playback event not recognised.")


class ConfigOptions:
    """
    Handles configuration options, including reading from disk (config.ini)
    """

    def __init__(self):
        self._REST_URL                 = ""
        self._REST_SUCCESS_CODE        = 200  # Standard HTTP success response code
        self._EVENTS                   = ""
        self._PB_NOTIF                 = ""
        self._PB_NOTIF_STOP            = -1
        self._PB_NOTIF_PLAY            = -1
        self._PB_NOTIF_PAUSE           = -1
        self._PB_NOTIF_ACTIVE_DEVICE   = -1
        self._PB_NOTIF_INACTIVE_DEVICE = -1
        self._POWER_OFF_DELAY_MINS     = 10

    @property
    def rest_url(self):
        return self._REST_URL

    @property
    def rest_success_code(self):
        return self._REST_SUCCESS_CODE

    @property
    def events(self):
        return self._EVENTS

    @property
    def pb_notif(self):
        return self._PB_NOTIF

    @property
    def pb_notif_stop(self):
        return self._PB_NOTIF_STOP

    @property
    def pb_notif_play(self):
        return self._PB_NOTIF_PLAY

    @property
    def pb_notif_pause(self):
        return self._PB_NOTIF_PAUSE

    @property
    def pb_notif_active_device(self):
        return self._PB_NOTIF_ACTIVE_DEVICE

    @property
    def pb_notif_inactive_device(self):
        return self._PB_NOTIF_INACTIVE_DEVICE

    @property
    def power_off_delay_mins(self):
        return self._POWER_OFF_DELAY_MINS

    def read_from_file(self):
        """
        Reads from config.ini in the same directory the necessary configuration params.
        """
        import configparser

        config = configparser.ConfigParser()
        config.optionxform = str

        # Check that the parser could read one file, and then extract the data.
        if "config.ini" in config.read("config.ini"):
            self._REST_URL                 = config.get("EventServer", "rest_url", fallback="")
            self._EVENTS                   = config.get("MediaFormat", "events", fallback="")
            self._PB_NOTIF                 = config.get("MediaFormat", "pb_notif", fallback="")
            self._PB_NOTIF_STOP            = config.getint("MediaFormat", "pb_notif_stop", fallback=-1)
            self._PB_NOTIF_PLAY            = config.getint("MediaFormat", "pb_notif_play", fallback=-1)
            self._PB_NOTIF_PAUSE           = config.getint("MediaFormat", "pb_notif_pause", fallback=-1)
            self._PB_NOTIF_ACTIVE_DEVICE   = config.getint("MediaFormat", "pb_notif_active_device", fallback=-1)
            self._PB_NOTIF_INACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_inactive_device", fallback=-1)
            self._POWER_OFF_DELAY_MINS     = config.getint("DeviceControl", "power_off_delay_mins", fallback=10)
        else:
            raise ValueError("Failed to open config.ini")

    def __str__(self):  # pragma: no cover
        """
        Returns a string with the current configuration.
        :return: str
        """

        ret = "".join(
            ["Configuration options\n=======================",
             "\nURL:                 ", self.rest_url,
             "\nEvents:              ", self.events,
             "\nPB notification:     ", self.pb_notif,
             "\nPB stop:             ", str(self.pb_notif_stop),
             "\nPB play:             ", str(self.pb_notif_play),
             "\nPB pause:            ", str(self.pb_notif_pause),
             "\nPB active device:    ", str(self.pb_notif_active_device),
             "\nPB inactive device:  ", str(self.pb_notif_inactive_device),
             "\nPB power off delay:  ", str(self.power_off_delay_mins)])

        return ret

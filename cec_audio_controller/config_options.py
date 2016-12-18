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

import configparser

class ConfigOptions:
    """
    Handles configuration options, including reading from disk (config.ini)
    """

    REST_URL                 = ""
    REST_SUCCESS_CODE        = 200      # Standard HTTP success response code
    EVENTS                   = ""
    PB_NOTIF                 = ""
    PB_NOTIF_STOP            = -1
    PB_NOTIF_PLAY            = -1
    PB_NOTIF_PAUSE           = -1
    PB_NOTIF_ACTIVE_DEVICE   = -1
    PB_NOTIF_INACTIVE_DEVICE = -1
    POWER_OFF_DELAY_MINS     = 10

    def read_from_file(self):
        """
        Reads from config.ini in the same directory the necessary configuration params.
        """

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

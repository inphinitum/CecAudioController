"""
Copyright 2016 Javier Martínez <javi@flamingalah.net>

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


class EventHandler:
    _controller = None
    _config = None

    def __init__(self, controller, config):
        """
        Default constructor

        :param controller: device_controller that will execute the commands
        :param config: config_options with REST message structure, power off delay...
        """

        self._controller = controller
        self._config = config

    def listen_for_events(self):
        """
        Listens on the given URL for events and dispatches the type of event
        to the right function for further processing.
        """

        while True:
            response = requests.get(self._config.REST_URL)

            if response.status_code == self._config.REST_SUCCESS_CODE:
                json_data = response.json()

                if self._config.EVENTS in json_data:
                    for event in json_data[self._config.EVENTS]:
                        if self._config.PB_NOTIF in event.keys():
                            self._process_playback_event(event)

    def _process_playback_event(self, event):
        """
        Processes the given playback event and triggers the respective command. Expects the
        following structure in events: {"Notification": int}.

        :param event: type of event to process
        """

        n_type = event[self._config.PB_NOTIF]

        if n_type == self._config.PB_NOTIF_PLAY or n_type == self._config.PB_NOTIF_ACTIVE_DEVICE:
            self._controller.power_on()
        elif n_type == self._config.PB_NOTIF_STOP:
            self._controller.standby()
        elif n_type == self._config.PB_NOTIF_INACTIVE_DEVICE:
            self._controller.delayed_standby(5)
        elif n_type == self._config.PB_NOTIF_PAUSE:
            self._controller.delayed_standby(self._config.POWER_OFF_DELAY_MINS * 60)

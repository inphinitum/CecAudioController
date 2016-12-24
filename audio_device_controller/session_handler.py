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


class SessionHandler:
    """
    This class holds the state of the player, and invokes commands on the configured device controller
    depending on if the session is active or not, content is being played or paused.
    """

    def __init__(self, dev_controller):
        self._pause_timer    = None
        self._active         = False
        self._dev_controller = dev_controller
        self._dev_on         = False

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def initialize(self):
        self._dev_controller.initialize()

    def cleanup(self):
        if self._pause_timer is not None:
            self._pause_timer.cancel()
            self._pause_timer = None

        self._dev_controller.standby()
        self._dev_controller.cleanup()
        self._dev_on = False

        self._active = False

    def active(self, new_active):
        """
        Sets the session to active.

        If the session was inactive it invokes power_on on the device controller.
        :param new_active: New session active state. True or False.
        :return: None
        """

        if self._active is False and new_active is True:
            self._dev_controller.power_on()
            self._dev_on = True

        elif self._active is True and new_active is False:
            # Cancel previous _pause_timer first
            if self._pause_timer is not None:
                self._pause_timer.cancel()
                self._pause_timer = None

            self._dev_controller.standby()
            self._dev_on = False

        self._active = new_active

    def play(self):
        """
        Session is now playing content.

        Only does something if the session is active and the device powered off. If the session was paused,
        the timer is cancelled.
        :return: None
        """

        if self._active:
            if self._pause_timer is not None:
                self._pause_timer.cancel()
                self._pause_timer = None

            if self._dev_on is False:
                self._dev_controller.power_on()
                self._dev_on = True

    def pause(self, seconds):
        """
        Session is now paused.

        Only does something if the session is active and the device powered on. If the session was paused,
        the command is ignored.
        :argument seconds: Number of seconds to wait until standby.
        :return: None
        """

        if self._active:
            from threading import Timer
            if self._pause_timer is None:
                self._pause_timer = Timer(seconds, self._callback_pause_timeout)
                self._pause_timer.start()

    def _callback_pause_timeout(self):
        """
        Callback for the timer started on pause().

        :return: None
        """

        if self._active and self._dev_on:
            self._dev_controller.standby()
            self._dev_on = False

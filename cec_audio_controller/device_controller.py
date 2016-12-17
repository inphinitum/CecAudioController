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

import subprocess
from threading import Timer


class CecError(Exception):
    """Exception class for Cec errors.
    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


class DeviceController:
    """
    Controller of devices that are cec-compatible.
    """

    _AUDIO_LOGICAL_ADDRESS = 5
    _cec_process           = None
    _cec_lib               = None
    _standby_timer         = None
    _config_params         = None

    def __init__(self):
        """
            Default constructor.

            Raises:
                CecError -- if the cec-client is not found in the system.
        """
        self._initialize_cec()

    def _initialize_cec(self):
        """
            Makes sure everything is initialized to control the audio device via CEC.

            Raises:
                CecError -- if the cec-client is not found in the system.
        """

        try:
            self._cec_process = subprocess.Popen(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self._init_audio_device()
        except OSError:
            raise CecError("cec-client not found.")

    def _init_audio_device(self):
        """
        Search for the audio device.

        Raises:
            CecError -- in case cec-client is unresponsive or audio device is not found.
        """

        try:
            output, error = self._cec_process.communicate(input="lad", timeout=15)

            if "logical address 5" not in output:
                raise CecError("cec-client does not find audio device.")

        except subprocess.TimeoutExpired:
            self._cec_process.kill()
            raise CecError("cec-client unresponsive, killed.")

    def power_on(self):
        """
        Power on the audio device.

        Raises:
             CecError -- in case cec-client is unresponsive.
        """

        print("Power ON requested")

        try:
            # If there was a timer, cancel and release.
            if self._standby_timer is not None:
                self._standby_timer.cancel()
                self._standby_timer = None

            self._cec_process.communicate(input="on 5", timeout=15)

        except subprocess.TimeoutExpired:
            self._cec_process.kill()
            raise CecError("cec-client unresponsive, killed.")

    def standby(self):
        """
        Put the audio device on standby.

        Raises:
            CecError -- in case cec-client is unresponsive.
        """

        print("STANDBY requested")

        try:
            # If there was a timer, cancel and release.
            if self._standby_timer is not None:
                self._standby_timer.cancel()
                self._standby_timer = None

            self._cec_process.communicate(input="standby 5", timeout=15)

        except subprocess.TimeoutExpired:
            self._cec_process.kill()
            raise CecError("cec-client unresponsive, killed.")

    def delayed_standby(self, seconds):
        """
        Put the audio device on standby after the given number of seconds. Used for
        temporary pauses, when switching off is annoying for the user. This action
        will be cancelled if a power_on or power_off command is received before the
        timer lapses.

        Raises:
            CecError -- in case cec-client is unresponsive.
        """

        print("Delayed STANDBY requested")

        # If there's already a timer, cancel it before starting a new one.
        if self._standby_timer is not None:
            self._standby_timer.cancel()
            self._standby_timer = Timer(seconds, self.standby)
            self._standby_timer.start()

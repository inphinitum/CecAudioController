"""
This file is part of cec_audio_controller.

cec_audio_controller is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

cec_audio_controller is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with cec_audio_controller.  If not, see <http://www.gnu.org/licenses/>.


This file provides a Python script to control a device via HDMI-CEC based
on events published via http

Depends on libcec <https://github.com/Pulse-Eight/libcec>

Author: Javier Martinez <javi@flamingalah.net>
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

        Makes sure everything is initialized to control the audio device via CEC.

        Raises:
            CecError -- if the cec-client is not found in the system.
        """

        try:
            _cec_process = subprocess.Popen(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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
            output = self._cec_process.communicate(input="lad", timeout=15)

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
            self._cec_process.communicate(input="on 5", timeout=15)

            # If there was a timer, cancel and release.
            if isinstance(self._standby_timer, Timer) and self._standby_timer.is_alive():
                self._standby_timer.cancel()

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
            self._cec_process.communicate(input="on 5", timeout=15)

            # If there was a timer, cancel and release.
            if isinstance(self._standby_timer, Timer) and self._standby_timer.is_alive():
                self._standby_timer.cancel()

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
        if isinstance(self._standby_timer, Timer) and self._standby_timer.is_alive():
            self._standby_timer.cancel()
            self._standby_timer = Timer(seconds, self.standby)
            self._standby_timer.start()

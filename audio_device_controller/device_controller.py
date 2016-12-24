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

import subprocess


class CecError(Exception):
    """Exception class for Cec errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


class DeviceController:
    """
    Base class for device controllers.
    """

    def __init__(self):
        """
        Default constructor.
        """
        pass

    def __enter__(self):
        """
        Initializes the controller.

        :return: self
        """
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up upon destruction.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return: None
        """
        self.cleanup()

    def initialize(self):
        """
        Base method for initializing the controller.

        :return: None
        """
        pass

    def cleanup(self):
        """
        Base method for cleaning up the object. Cancels any ongoing timer.

        :return: None
        """
        pass

    def power_on(self):
        """
        Make sure an pending delayed_standby is cancelled.

        :return: None
        """
        pass

    def standby(self):
        """
        Make sure any pending delayed_standby is cancelled.

        :return: None
        """
        pass


class DeviceControllerCec(DeviceController):
    """
    Controller of devices that are cec-compatible.
    """

    def __init__(self):
        super().__init__()

        self._AUDIO_LOGICAL_ADDRESS = 5
        self._cec_process           = None
        self._cec_lib               = None

    def initialize(self):
        """
        Makes sure everything is initialized to control the audio device via CEC.

        Raises:
            CecError -- if the cec-client is not found in the system.
        """
        super().initialize()

        if self._cec_process is None:
            try:
                self._cec_process = subprocess.Popen(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

                try:
                    output, error = self._cec_process.communicate(input="lad", timeout=15)
                    if "logical address 5" not in output:
                        raise CecError("cec-client does not find audio device.")

                except subprocess.TimeoutExpired:
                    raise CecError("cec-client unresponsive, terminated.")
            except OSError:
                raise CecError("cec-client not found.")

    def cleanup(self):
        """
        Clean up all spawned threads.

        :return: None
        """
        super().cleanup()

        # Stop the thread for the cec-tool
        if self._cec_process is not None and callable(getattr(self._cec_process, "terminate")):
            self._cec_process.terminate()
            self._cec_process = None

    def power_on(self):
        """
        Power on the audio device.

        Raises:
             CecError -- in case cec-client is unresponsive.

        :return: None
        """
        super().power_on()
        try:
            self._cec_process.communicate(input="on 5", timeout=15)

        except subprocess.TimeoutExpired:
            self._cec_process.terminate()
            raise CecError("cec-client unresponsive, terminated.")

    def standby(self):
        """
        Put the audio device on standby.

        Raises:
            CecError -- in case cec-client is unresponsive.

        :return: None
        """
        super().standby()
        try:
            self._cec_process.communicate(input="standby 5", timeout=15)

        except subprocess.TimeoutExpired:
            self._cec_process.terminate()
            raise CecError("cec-client unresponsive, killed.")

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

import unittest
import subprocess
from threading import Timer
from unittest.mock import Mock

from cec_audio_controller.device_controller import DeviceController


class DeviceHandlerTest(unittest.TestCase):

    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def test_power_on(self, mock_popen):
        """
            Test single command power_on.

        :param mock_popen: the mock object for Popen
        :return: nothing
        """

        controller = self.init_controller(mock_popen)

        # Control that the command to power on the audio device is sent, and timer not cancelled
        mock_popen.communicate.return_value = ("", "")
        controller.power_on()
        mock_popen.communicate.assert_called_with(input="on 5", timeout=15)

    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def test_standby(self, mock_popen):
        """
            Test single command standby.

        :param mock_popen: the mock object for Popen
        :return: nothing
        """

        controller = self.init_controller(mock_popen)

        # Control that the command to standby the audio device is sent, and timer not cancelled
        mock_popen.communicate.return_value = ("", "")
        controller.standby()
        mock_popen.communicate.assert_called_with(input="standby 5", timeout=15)

    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def test_power_on_with_delayed_stby(self, mock_popen):
        """
            Test single command power_on while there was a pending delayed_standby.

        :param mock_popen: the mock object for Popen
        :param mock_timer: the mock object for Timer
        :return: nothing
        """

        controller = self.init_controller(mock_popen)
        mock_timer = Mock()
        controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        mock_popen.communicate.return_value = ("", "")
        controller.power_on()
        mock_popen.communicate.assert_called_with(input="on 5", timeout=15)
        mock_timer.cancel.assert_called_with()
        self.assertIsNone(controller._standby_timer)

    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def test_standby_with_delayed_stby(self, mock_popen):
        """
            Test single command power_on while there was a pending delayed_standby.

        :param mock_popen: the mock object for Popen
        :param mock_timer: the mock object for Timer
        :return: nothing
        """

        controller = self.init_controller(mock_popen)
        mock_timer = Mock()
        controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        mock_popen.communicate.return_value = ("", "")
        controller.standby()
        mock_popen.communicate.assert_called_with(input="standby 5", timeout=15)
        mock_timer.cancel.assert_called_with()
        self.assertIsNone(controller._standby_timer)

    def init_controller(self, mock_popen):
        """
            Boilerplate code to initialize the controller.

        :param mock_popen: the mock object for Popen
        :return: the newly created controller
        """
        mock_popen.return_value = mock_popen
        mock_popen.communicate.return_value = ("logical address 5", "")

        # Control the cec-client is invoked properly, audio device searched and found
        controller = DeviceController()
        mock_popen.assert_called_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        mock_popen.communicate.assert_called_with(input="lad", timeout=15)

        return controller

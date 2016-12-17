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
from unittest.mock import Mock


class DeviceHandlerTest(unittest.TestCase):
    """
    Unit tests for the DeviceHandler class in cec_audio_controller.
    """

    def test_power_on(self):
        """
        Test single command power_on.

        :return: nothing
        """

        controller = self.init_controller()

        # Control that the command to power on the audio device is sent, and timer not cancelled
        controller._cec_process.communicate.return_value = ("", "")
        controller.power_on()
        controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)

    def test_standby(self):
        """
        Test single command standby.

        :return: nothing
        """

        controller = self.init_controller()

        # Control that the command to standby the audio device is sent, and timer not cancelled
        controller._cec_process.communicate.return_value = ("", "")
        controller.standby()
        controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)

    def test_power_on_with_delayed_stby(self):
        """
        Test single command power_on while there was a pending delayed_standby.

        :return: nothing
        """

        controller = self.init_controller()
        mock_timer = Mock()
        controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        controller._cec_process.communicate.return_value = ("", "")
        controller.power_on()
        controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)
        mock_timer.cancel.assert_called_with()
        self.assertIsNone(controller._standby_timer)

    def test_standby_with_delayed_stby(self):
        """
        Test single command power_on while there was a pending delayed_standby.

        :return: nothing
        """

        controller = self.init_controller()
        mock_timer = Mock()
        controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        controller._cec_process.communicate.return_value = ("", "")
        controller.standby()
        controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)
        mock_timer.cancel.assert_called_once_with()
        self.assertIsNone(controller._standby_timer)

    @unittest.mock.patch("threading.Timer", autospec=True)
    def test_delayed_standby(self, mock_timer):
        """
        Test single command delayed_standby.

        :param mock_timer: the mock object for Timer
        :return: nothing
        """

        controller = self.init_controller()
        mock_timer.return_value = mock_timer

        controller.delayed_standby(10)
        mock_timer.start.assert_called_once_with()
        mock_timer.reset_mock()

    @unittest.mock.patch("threading.Timer", autospec=True)
    def test_delayed_standby_with_delayed_standby(self, mock_timer):
        """
        Test single command delayed_standby when there was a pending delayed_standby.

        :param mock_timer: the mock object for Timer
        :return: nothing
        """

        mock_timer.reset_mock()
        controller = self.init_controller()
        mock_timer.return_value = mock_timer

        # Setup previous timer...
        controller._standby_timer = mock_timer

        controller.delayed_standby(10)
        mock_timer.cancel.assert_called_once_with()
        controller._standby_timer.start.assert_called_once_with()

    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def init_controller(self, mock_popen):
        """
        Boilerplate code to initialize the controller.

        :param mock_popen: the mock object for Popen
        :return: the newly created controller
        """
        mock_popen.return_value = mock_popen
        mock_popen.communicate.return_value = ("logical address 5", "")

        # Control the cec-client is invoked properly, audio device searched and found
        import subprocess
        from cec_audio_controller.device_controller import DeviceController
        controller = DeviceController()
        mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)

        return controller

class EventHandlerTest(unittest.TestCase):
    """
    Unit tests for the EventHandler class in cec_audio_controller.
    """

    def setUp(self):
        self.controller = Mock()
        self.config = Mock()
        self.ev_handler = EventHandler(self.controller, self.config)


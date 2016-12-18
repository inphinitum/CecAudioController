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

import unittest
from unittest.mock import Mock

from cec_audio_controller.event_handler import EventHandler
from cec_audio_controller.event_handler import EventError


class DeviceHandlerTest(unittest.TestCase):
    """
    Unit tests for the DeviceHandler class in cec_audio_controller.
    """

    @unittest.mock.patch("threading.Timer", autospec=True)
    @unittest.mock.patch("subprocess.Popen", autospec=True)
    def setUp(self, mock_popen, mock_timer):
        """
        Boilerplate code to initialize the controller.

        :param mock_popen: the mock object for Popen
        :return: None
        """
        mock_popen.return_value = mock_popen
        mock_popen.communicate.return_value = ("logical address 5", "")
        mock_timer.return_value = mock_timer

        # Control the cec-client is invoked properly, audio device searched and found
        import subprocess
        from cec_audio_controller.device_controller import DeviceController
        self.controller = DeviceController()
        mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)

    def test_power_on(self):
        """
        Test single command power_on.

        :return: None
        """

        # Control that the command to power on the audio device is sent, and timer not cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.power_on()
        self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)

    def test_standby(self):
        """
        Test single command standby.

        :return: None
        """

        # Control that the command to standby the audio device is sent, and timer not cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.standby()
        self.controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)

    def test_power_on_with_delayed_stby(self):
        """
        Test single command power_on while there was a pending delayed_standby.

        :return: None
        """

        mock_timer = Mock()
        self.controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.power_on()
        self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)
        mock_timer.cancel.assert_called_with()
        self.assertIsNone(self.controller._standby_timer)

    def test_standby_with_delayed_stby(self):
        """
        Test single command power_on while there was a pending delayed_standby.

        :return: None
        """

        mock_timer = Mock()
        self.controller._standby_timer = mock_timer

        # Control that the command to power on the audio device is sent, and timer cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.standby()
        self.controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)
        mock_timer.cancel.assert_called_once_with()
        self.assertIsNone(self.controller._standby_timer)

    @unittest.mock.patch("threading.Timer", autospec=True)
    def test_delayed_standby(self, mock_timer):
        """
        Test single command delayed_standby.

        :param mock_timer: the mock object for Timer
        :return: None
        """

        mock_timer.return_value = mock_timer

        self.controller.delayed_standby(10)
        self.controller._standby_timer.start.assert_called_once_with()
        self.controller._standby_timer.reset_mock()

    @unittest.mock.patch("threading.Timer", autospec=True)
    def test_delayed_standby_with_delayed_standby(self, mock_timer):
        """
        Test single command delayed_standby when there was a pending delayed_standby.

        :param mock_timer: the mock object for Timer
        :return: None
        """

        mock_timer.reset_mock()
        mock_timer.return_value = mock_timer

        # Setup previous timer...
        self.controller._standby_timer = mock_timer

        self.controller.delayed_standby(10)
        mock_timer.cancel.assert_called_once_with()
        self.controller._standby_timer.start.assert_called_once_with()


class EventHandlerTest(unittest.TestCase):
    """
    Unit tests for the EventHandler class in cec_audio_controller.
    """

    def setUp(self):
        self.mock_controller                      = Mock()
        self.mock_config                          = Mock()
        self.mock_config.EVENTS                   = "Events"
        self.mock_config.PB_NOTIF                 = "Notification"
        self.mock_config.PB_NOTIF_STOP            = 0
        self.mock_config.PB_NOTIF_PLAY            = 1
        self.mock_config.PB_NOTIF_PAUSE           = 2
        self.mock_config.PB_NOTIF_ACTIVE_DEVICE   = 3
        self.mock_config.PB_NOTIF_INACTIVE_DEVICE = 4
        self.mock_config.POWER_OFF_DELAY_MINS     = 10

        self.ev_handler = EventHandler(self.mock_controller, self.mock_config)

    def test_incorrect_response_format(self):
        """
        Tests that the event handler processes json responses correctly.

        Correct single event:    {"Events":[{"Notification": 1}]}
        Correct multiple events: {"Events":[{"Notification": 1}, {"Notification": 0}, {"Notification": 4}]}

        :return: None
        """

        # EVENTS top element not present
        json = {"Ev": [{"Notif": 0}]}

        with self.assertRaises(EventError) as context:
            self.ev_handler.process_json_response(json)
        self.assertTrue("JSON response malformed." in str(context.exception))

    def test_single_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly.

        :return: None
        """

        # Stop
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_STOP}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.standby.assert_called_once_with()
        self.mock_controller.reset_mock()

        # Play
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_PLAY}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.power_on.assert_called_once_with()
        self.mock_controller.reset_mock()

        # Pause
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_PAUSE}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.delayed_standby.assert_called_once_with(self.mock_config.POWER_OFF_DELAY_MINS*60)
        self.mock_controller.reset_mock()

        # Active device
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_ACTIVE_DEVICE}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.power_on.assert_called_once_with()
        self.mock_controller.reset_mock()

        # Inactive device
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_INACTIVE_DEVICE}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.delayed_standby.assert_called_once_with(self.mock_config.POWER_OFF_DELAY_MINS)
        self.mock_controller.reset_mock()

    def test_several_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly if received in the same json.

        :return: None
        """

        # Stop, play, pause, active device, inactive device
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_STOP},
                                          {self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_PLAY},
                                          {self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_PAUSE},
                                          {self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_ACTIVE_DEVICE},
                                          {self.mock_config.PB_NOTIF: self.mock_config.PB_NOTIF_INACTIVE_DEVICE}]}

        self.ev_handler.process_json_response(json)
        self.assertTrue(self.mock_controller.power_on.call_count == 2)
        self.assertTrue(self.mock_controller.standby.call_count == 1)
        self.assertTrue(self.mock_controller.delayed_standby.call_count == 2)

        self.mock_controller.reset_mock()

    def test_single_unknown_pb_events(self):
        """
        Tests that the event handler handles unknown playback events correctly.

        :return: None
        """

        # Unknown event type, should be ignored
        json = {self.mock_config.EVENTS: [{self.mock_config.PB_NOTIF: -1}]}
        self.ev_handler.process_json_response(json)
        self.mock_controller.power_on.assert_not_called()
        self.mock_controller.standby.assert_not_called()
        self.mock_controller.delayed_standby.assert_not_called()
        self.mock_controller.reset_mock()

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
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import call

from cec_audio_controller.event_handler import EventError
from cec_audio_controller.event_handler import EventHandler
from cec_audio_controller.config_options import ConfigOptions


class DeviceHandlerTest(unittest.TestCase):
    """
    Unit tests for the DeviceHandler class in cec_audio_controller.
    """

    def setUp(self):
        """
        Boilerplate code to initialize the controller.

        :return: None
        """

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            # Control the cec-client is invoked properly, audio device searched and found
            import subprocess
            from cec_audio_controller.device_controller import DeviceController

            self.controller = DeviceController()
            mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)

    def tearDown(self):
        """
        Undo setUp, leave things clean.

        :return: None
        """

        self.controller._cleanup()

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

    def test_delayed_standby(self):
        """
        Test single command delayed_standby.

        :return: None
        """

        with patch("threading.Timer", autospec=True) as mock_timer:
            mock_timer.return_value.return_value = mock_timer

            self.assertIsNone(self.controller._standby_timer)
            self.controller.delayed_standby(10)
            self.controller._standby_timer.start.assert_called_once_with()

    def test_delayed_standby_with_delayed_standby(self):
        """
        Test single command delayed_standby when there was a pending delayed_standby.

        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            # Simulate there was a previous timer.
            self.controller._standby_timer = mock_timer

            self.controller.delayed_standby(10)
            mock_timer.cancel.assert_called_once_with()
            self.controller._standby_timer.start.assert_called_once_with()

    def test_sequence_1(self):
        """
        Test sequence play-delayed_standby-play before timer goes off.

        :return:
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            self.controller.power_on()
            self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)

            self.controller.delayed_standby(10)
            self.controller._standby_timer.start.assert_called_once_with()

            # Previous delayed_standby() is still active, the timer is cancelled and no cec command is executed.
            self.controller.power_on()
            mock_timer.cancel.assert_called_once_with()

    def test_sequence_2(self):
        """
        Test sequence play-delayed_standby-standby-play

        :return:
        """

        with patch("threading.Timer"):
            self.controller.power_on()
            self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)

            self.controller.delayed_standby(10)
            self.controller._standby_timer.start.assert_called_once_with()

            # When timer goes of it calls standby()
            mock_timer = self.controller._standby_timer
            self.controller.standby()
            mock_timer.cancel.assert_called_once_with()
            self.controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)

            self.controller.power_on()
            self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)


class EventHandlerTest(unittest.TestCase):
    """
    Unit tests for the EventHandler class in cec_audio_controller.
    """

    def setUp(self):
        """
        Initialization for test cases.

        :return: None
        """

        self.mock_controller                      = Mock()
        self.mock_config                          = Mock()
        self.mock_config.REST_URL                 = "http://localhost:4444/test"
        self.mock_config.REST_SUCCESS_CODE        = 200
        self.mock_config.REST_NOT_FOUND_CODE      = 404
        self.mock_config.EVENTS                   = "Events"
        self.mock_config.PB_NOTIF                 = "Notification"
        self.mock_config.PB_NOTIF_STOP            = 0
        self.mock_config.PB_NOTIF_PLAY            = 1
        self.mock_config.PB_NOTIF_PAUSE           = 2
        self.mock_config.PB_NOTIF_ACTIVE_DEVICE   = 3
        self.mock_config.PB_NOTIF_INACTIVE_DEVICE = 4
        self.mock_config.POWER_OFF_DELAY_MINS     = 10

        self.ev_handler = EventHandler(self.mock_controller, self.mock_config)

    def test_not_json(self):
        """
        Tests the case when the response cannot be parsed as json.

        :return: None
        """

        with self.assertRaises(EventError) as context:
            response = "0123456789"
            self.ev_handler.process_json_response(response)
            self.assertTrue("Response from " in str(context.exception))

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

    def test_listen_for_events_200(self):
        """
        Tests the event listening functionality in the handler, both successful and unsuccessful.

        :return: None
        """

        with patch("requests.get") as get_mock:
            self.mock_requests_get = get_mock
            self.mock_requests_get.return_value.status_code = self.mock_config.REST_SUCCESS_CODE
            with self.assertRaises(EventError) as context:
                self.ev_handler.listen_for_events()
                self.assertTrue("JSON response malformed." in str(context.exception))

    def test_listen_for_events_400(self):
        """
        Tests that the event listener works as intended in case there's a problem reaching the endpoint.

        :return: None
        """

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = self.mock_config.REST_NOT_FOUND_CODE
            with self.assertRaises(EventError) as context:
                self.ev_handler.listen_for_events()
                self.assertTrue("does not respond: Status code" in str(context.exception))


class ConfigOptionsTest(unittest.TestCase):
    """
    Tests for the ConfigOptions class.
    """

    def setUp(self):
        """
        Initialization for test cases.

        :return: None
        """

        self.config_options = ConfigOptions()

    def test_read_from_file(self):
        """
        Test that all the elements that should be read are read properly from .config.ini

        :return: None
        """

        with patch("configparser.ConfigParser") as mock_parser:
            mock_parser.return_value.read.return_value = ["config.ini"]
            mock_parser.return_value.has_option.side_effect = ["EventServer", "MediaFormat", "MediaFormat",
                                                               "MediaFormat", "MediaFormat", "MediaFormat",
                                                               "MediaFormat", "MediaFormat", "DeviceControl"]
            mock_parser.return_value.get.side_effect = ["http://localhost:5555/ev", "Events", "Notification"]
            mock_parser.return_value.getint.side_effect = [0, 1, 2, 3, 4, 10]

            self.config_options.read_from_file()

            mock_parser.return_value.read.assert_called_once_with("config.ini")

            # Parser has been asked about the right things have.
            calls = [call("EventServer", "rest_url"), call("MediaFormat", "events"), call("MediaFormat", "pb_notif"),
                     call("MediaFormat", "pb_notif_stop"), call("MediaFormat", "pb_notif_play"),
                     call("MediaFormat", "pb_notif_pause"), call("MediaFormat", "pb_notif_active_device"),
                     call("MediaFormat", "pb_notif_inactive_device"), call("DeviceControl", "power_off_delay_mins")]
            mock_parser.return_value.has_option.assert_has_calls(calls)

            # Parser has been queried about the right things.
            calls = [call("MediaFormat", "events"), call("MediaFormat", "pb_notif")]
            mock_parser.return_value.get.assert_has_calls(calls)

            calls = [call("MediaFormat", "pb_notif_stop"), call("MediaFormat", "pb_notif_play"),
                     call("MediaFormat", "pb_notif_pause"), call("MediaFormat", "pb_notif_active_device"),
                     call("MediaFormat", "pb_notif_inactive_device"), call("DeviceControl", "power_off_delay_mins")]
            mock_parser.return_value.getint.assert_has_calls(calls)

            # Stored values match the provided data.
            self.assertTrue(self.config_options.REST_URL == "http://localhost:5555/ev")
            self.assertTrue(self.config_options.EVENTS == "Events")
            self.assertTrue(self.config_options.PB_NOTIF == "Notification")
            self.assertTrue(self.config_options.PB_NOTIF_STOP == 0)
            self.assertTrue(self.config_options.PB_NOTIF_PLAY == 1)
            self.assertTrue(self.config_options.PB_NOTIF_PAUSE == 2)
            self.assertTrue(self.config_options.PB_NOTIF_ACTIVE_DEVICE == 3)
            self.assertTrue(self.config_options.PB_NOTIF_INACTIVE_DEVICE == 4)
            self.assertTrue(self.config_options.POWER_OFF_DELAY_MINS == 10)

    def test_read_from_empty_file(self):
        """
        Test when reading from an empty file.

        :return: None
        """

        with patch("configparser.ConfigParser") as mock_parser:
            mock_parser.return_value.read.return_value = ["config.ini"]
            mock_parser.return_value.has_option.return_value = False

            self.config_options.read_from_file()

            mock_parser.return_value.read.assert_called_once_with("config.ini")

            calls = [call("EventServer", "rest_url"), call("MediaFormat", "events"), call("MediaFormat", "pb_notif"),
                     call("MediaFormat", "pb_notif_stop"), call("MediaFormat", "pb_notif_play"),
                     call("MediaFormat", "pb_notif_pause"), call("MediaFormat", "pb_notif_active_device"),
                     call("MediaFormat", "pb_notif_inactive_device"), call("DeviceControl", "power_off_delay_mins")]
            mock_parser.return_value.has_option.assert_has_calls(calls)
            mock_parser.return_value.get.assert_not_called()
            mock_parser.return_value.getint.assert_not_called()

    def test_file_not_found(self):
        """
        Thest behaviour when config file is not found.

        :return:
        """

        with self.assertRaises(ValueError) as context:
            self.config_options.read_from_file()
            self.assertTrue("Failed to open config.ini" in str(context.exception))

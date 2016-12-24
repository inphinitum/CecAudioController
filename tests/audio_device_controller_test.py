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

from audio_device_controller.event_handler import EventError
from audio_device_controller.event_handler import EventHandler
from audio_device_controller.config_options import ConfigOptions
from audio_device_controller.session_handler import SessionHandler


class SessionHandlerTest(unittest.TestCase):
    """
    Unit tests for the PlayerDeviceCoordinator class in audio_device_controller.
    """

    def match_internal_state(self, session, expected_state):
        """
        Help method to check that the internal state of the passed SessionHandler matches the expected one.

        :argument session: The session to be evaluated
        :argument expected_state: "Inactive, "Active", "ShortPause", "Playing", "LongPause", "Clean"
        :return: True if it's a match, False otherwise.
        """

        ret = False

        if expected_state is "Inactive":
            ret = session._active is False and \
                  session._pause_timer is None and \
                  session._dev_on is False

        elif expected_state is "ShortPause":
            ret = session._active is True and \
                  session._pause_timer is not None and \
                  session._dev_on is True

        elif expected_state is "Playing" or expected_state is "Active":
            ret = session._active is True and \
                  session._pause_timer is None and \
                  session._dev_on is True

        elif expected_state is "LongPause":
            ret = session._active is True and \
                  session._pause_timer is None and \
                  session._dev_on is False

        return ret

    def test_enter_exit(self):
        """
        Test that all the resources are correctly initialized and released.

        The device controller should be initialized and cleaned-up, pause timer should be cancelled and None-ed.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl):
                mock_dev_ctrl.initialize.assert_called_once_with()

            mock_dev_ctrl.standby.assert_called_once_with()
            mock_dev_ctrl.cleanup.assert_called_once_with()
            mock_dev_ctrl.reset_mock()

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.play()
                session.pause(10)

            mock_dev_ctrl.standby.assert_called_once_with()
            mock_dev_ctrl.cleanup.assert_called_once_with()
            mock_timer.cancel.assert_called_once_with()
            self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_player_active_prev_inactive(self):
        """
        Test active command when session was inactive.

        power_on() shall be invoked.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(True)
            mock_dev_ctrl.power_on.assert_called_with()
            mock_dev_ctrl.standby.assert_not_called()
            self.assertTrue(self.match_internal_state(session, "Active"))

    def test_player_active_prev_active(self):
        """
        Test active command when session was already active.

        Nothing should happen.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(True)
            mock_dev_ctrl.reset_mock()

            session.active(True)
            mock_dev_ctrl.power_on.assert_not_called()
            mock_dev_ctrl.standby.assert_not_called()

            self.assertTrue(self.match_internal_state(session, "Active"))

    def test_player_inactive_prev_active(self):
        """
        Test inactive command when session was active.

        standby() should be called().
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(True)
            mock_dev_ctrl.reset_mock()

            session.active(False)
            mock_dev_ctrl.power_on.assert_not_called()
            mock_dev_ctrl.standby.assert_called_once_with()

            self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_player_inactive_prev_inactive(self):
        """
        Test inactive command when session was already inactive.

        Nothing should happen.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(False)
            mock_dev_ctrl.power_on.assert_not_called()
            mock_dev_ctrl.standby.assert_not_called()

            self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_player_inactive_prev_pause(self):
        """
        Test inactive command when session was active and paused.

        Timer for pause should be cancelled, standby() invoked.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)
                mock_dev_ctrl.reset_mock()
                mock_timer.reset_mock()

                session.active(False)
                mock_timer.cancel.assert_called_once_with()
                self.assertIs(session._pause_timer, None)
                mock_dev_ctrl.power_on.assert_not_called()
                mock_dev_ctrl.standby.assert_called_once_with()

                self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_play_active(self):
        """
        Test play command when session is active and not paused.

        Nothing should happen.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(True)
            mock_dev_ctrl.reset_mock()

            session.play()
            mock_dev_ctrl.power_on.assert_not_called()
            mock_dev_ctrl.standby.assert_not_called()

            self.assertTrue(self.match_internal_state(session, "Playing"))

    def test_play_active_prev_pause(self):
        """
        Test play command when session is active and pause has expired.

        The audio device is on standby, so power_on() should be invoked.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.active(True)
            session._callback_pause_timeout()
            mock_dev_ctrl.reset_mock()

            session.play()
            mock_dev_ctrl.power_on.assert_called_with()
            mock_dev_ctrl.standby.not_called()

            self.assertTrue(self.match_internal_state(session, "Playing"))

    def test_play_active_prev_pending_pause(self):
        """
        Test play command when session is active and paused (not yet expired).

        Scheduled standby() should be cancelled and no new power_on should be invoked.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)
                mock_dev_ctrl.reset_mock()

                session.play()
                mock_timer.cancel.called_once_with_args()
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                self.assertTrue(self.match_internal_state(session, "Playing"))

    def test_play_inactive(self):
        """
        Test play command when session is inactive.

        Nothing should happen.
        :return: None
        """

        from audio_device_controller.device_controller import DeviceController
        mock_dev_ctrl = Mock(spec=DeviceController)

        with SessionHandler(mock_dev_ctrl) as session:
            session.play()
            mock_dev_ctrl.power_on.not_called()
            mock_dev_ctrl.standby.not_called()

            self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_pause_active(self):
        """
        Test pause command when session is active.

        A timer should be started to invoke standby() on the device controller.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)

                mock_timer.start.called_once_with_args(10, session._callback_pause_timeout)
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                self.assertTrue(self.match_internal_state(session, "ShortPause"))

    def test_long_pause_active(self):
        """
        Test pause command when session is active.

        A timer should be started to invoke standby() on the device controller.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)

                mock_timer.start.called_once_with_args(10, session._callback_pause_timeout)
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                # Timer goes off
                session._callback_pause_timeout()
                mock_dev_ctrl.standby.assert_called_once_with()

                self.assertTrue(self.match_internal_state(session, "LongPause"))

    def test_pause_active_prev_pause(self):
        """
        Test pause command when session is active and there was a previous pause.

        Nothing should happen.
        :return:
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)
                mock_timer.reset_mock()

                session.pause(10)
                mock_timer.cancel.assert_not_called()
                mock_timer.start.assert_not_called()
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                self.assertTrue(self.match_internal_state(session, "ShortPause"))

    def test_pause_inactive(self):
        """
        Test pause command when session is inactive.

        Nothing should happen, no timer should be started.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.device_controller import DeviceController
            mock_dev_ctrl = Mock(spec=DeviceController)

            with SessionHandler(mock_dev_ctrl) as session:
                session.pause(10)
                self.assertIsNone(session._pause_timer)
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                self.assertTrue(self.match_internal_state(session, "Inactive"))


class DeviceControllerCecTest(unittest.TestCase):
    """
    Unit tests for the DeviceControllerCec class in audio_device_controller.
    """

    def setUp(self):
        """
        Boilerplate code to initialize the controller.

        :return: None
        """

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            # Control the cec-client is invoked properly, audio device searched and found
            import subprocess
            from audio_device_controller.device_controller import DeviceControllerCec

            self.controller = DeviceControllerCec()
            self.controller.initialize()
            self.controller._cec_process.assert_called_once_with(["cec-client"],
                                                                 stdin=subprocess.PIPE,
                                                                 stdout=subprocess.PIPE)
            mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)

    def tearDown(self):
        """
        Undo setUp, leave things clean.

        :return: None
        """

        self.controller.cleanup()

    def test_power_on(self):
        """
        Test single command power_on.

        :return: None
        """

        # Control that the command to power on the audio device is sent, and timer not cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.power_on()
        self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)

    def test_power_on_cec_fail(self):
        """
        Test single command power_on with failure to communicate with cec.

        :return: None
        """

        # Control that the command to power on the audio device is sent, and timer not cancelled
        from audio_device_controller.device_controller import CecError
        from subprocess import TimeoutExpired

        self.controller._cec_process.communicate.side_effect = TimeoutExpired("lad", 15)
        with self.assertRaises(CecError) as context:
            self.controller.power_on()
        self.controller._cec_process.communicate.assert_called_with(input="on 5", timeout=15)
        self.assertTrue("cec-client unresponsive" in str(context.exception))

    def test_standby(self):
        """
        Test single command standby.

        :return: None
        """

        # Control that the command to standby the audio device is sent, and timer not cancelled
        self.controller._cec_process.communicate.return_value = ("", "")
        self.controller.standby()
        self.controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)

    def test_standby_cec_fail(self):
        """
        Test single command standby with failure to communicate with cec.

        :return: None
        """

        # Control that the command to standby the audio device is sent, and timer not cancelled
        from audio_device_controller.device_controller import CecError
        from subprocess import TimeoutExpired

        self.controller._cec_process.communicate.side_effect = TimeoutExpired("standby 5", 15)
        with self.assertRaises(CecError) as context:
            self.controller.standby()
        self.controller._cec_process.communicate.assert_called_with(input="standby 5", timeout=15)
        self.assertTrue("cec-client unresponsive" in str(context.exception))


class DeviceControllerInitCleanupTest(unittest.TestCase):
    """
    Test class to test basic initialization and cleanup.
    """

    def test_initialize_no_cec(self):
        """
        Test when the initialization fails due to non-existing cec controller.

        :return: None
        """
        with patch("subprocess.Popen", spec=True) as mock_popen:
            # Control the cec-client is invoked properly, audio device searched and found.
            from audio_device_controller.device_controller import DeviceControllerCec
            from audio_device_controller.device_controller import CecError

            mock_popen.side_effect = OSError()

            with self.assertRaises(CecError) as context:
                controller = DeviceControllerCec()
                controller.initialize()
            self.assertTrue("cec-client not found." in str(context.exception))

    def test_initialize_no_audio(self):
        """
        Test when there's no audio device connected to the hdmi bus.

        :return: None
        """
        with patch("subprocess.Popen", spec=True) as mock_popen:
            # Control the cec-client is invoked properly, audio device searched and found.
            from audio_device_controller.device_controller import DeviceControllerCec
            from audio_device_controller.device_controller import CecError

            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("", "")

            with self.assertRaises(CecError) as context:
                controller = DeviceControllerCec()
                controller.initialize()

            self.assertTrue("cec-client does not find audio device." in str(context.exception))

    def test_init_audio_cec_fail(self):
        """
        Test initialization of audio failing due to unresponsive cec.

        :return: None
        """

        with patch("subprocess.Popen", spec=True) as mock_popen:
            from subprocess import TimeoutExpired
            mock_popen.return_value = mock_popen
            mock_popen.return_value.communicate.side_effect = TimeoutExpired("lad", 15)

            # Control the cec-client is invoked properly, audio device searched and found
            import subprocess
            from audio_device_controller.device_controller import DeviceControllerCec

            from audio_device_controller.device_controller import CecError
            with self.assertRaises(CecError) as context:
                self.controller = DeviceControllerCec()
                self.controller.initialize()
            mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)
            self.assertTrue("cec-client unresponsive, terminated." in str(context.exception))

    @staticmethod
    def test_cleanup_before_initialization():
        """
        Test no action is taken if cleanup is called before initialization.

        :return: None
        """

        from audio_device_controller.device_controller import DeviceControllerCec

        # If something is wrong an exception will be raised...
        controller = DeviceControllerCec()
        controller.cleanup()

    @staticmethod
    def test_initialize_twice():
        """
        Test that initialization of an already-initialized controller doesn't do anything.

        :return: None
        """

        from audio_device_controller.device_controller import DeviceControllerCec

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            with DeviceControllerCec() as controller:
                # Control the cec-client is invoked properly, audio device searched and found
                import subprocess
                mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)
                mock_popen.reset_mock()

                # Second (not needed) initialization.
                controller.initialize()
                mock_popen.assert_not_called()
                mock_popen.communicate.assert_not_called()


class EventHandlerTest(unittest.TestCase):
    """
    Unit tests for the EventHandler class in audio_device_controller.
    """

    def setUp(self):
        """
        Initialization for test cases.

        :return: None
        """

        from audio_device_controller.session_handler import SessionHandler
        from audio_device_controller.config_options import ConfigOptions

        self.mock_session                          = Mock(spec=SessionHandler)
        self.mock_config                           = Mock(spec=ConfigOptions)
        self.mock_config._REST_URL                 = "http://localhost:4444/test"
        self.mock_config._REST_SUCCESS_CODE        = 200
        self.mock_config._REST_NOT_FOUND_CODE      = 404
        self.mock_config._EVENTS                   = "Events"
        self.mock_config._PB_NOTIF                 = "Notification"
        self.mock_config._PB_NOTIF_STOP            = 0
        self.mock_config._PB_NOTIF_PLAY            = 1
        self.mock_config._PB_NOTIF_PAUSE           = 2
        self.mock_config._PB_NOTIF_ACTIVE_DEVICE   = 3
        self.mock_config._PB_NOTIF_INACTIVE_DEVICE = 4
        self.mock_config._POWER_OFF_DELAY_MINS     = 10

        self.ev_handler = EventHandler(self.mock_session, self.mock_config)
        self.mock_session.active(True)
        self.mock_session.reset_mock()

    def tearDown(self):
        self.mock_session.cleanup()

    def test_not_json(self):
        """
        Tests the case when the response cannot be parsed as json.

        :return: None
        """

        with self.assertRaises(EventError) as context:
            response = "0123456789"
            self.ev_handler.process_json_response(response)
        self.assertTrue("Response malformed." in str(context.exception))

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
        self.assertTrue("Response malformed." in str(context.exception))
        self.mock_session.play.assert_not_called()
        self.mock_session.pause.assert_not_called()
        self.mock_session.active.assert_not_called()

    def test_not_recognised_events(self):
        """
        Test behaviour when JSON is correctly formed but events are not recognised.

        :return: None
        """

        # EVENTS top element not present
        json = {"Events": [{"Notif": 0}]}

        self.ev_handler.process_json_response(json)
        self.mock_session.play.assert_not_called()
        self.mock_session.pause.assert_not_called()
        self.mock_session.active.assert_not_called()

    def test_single_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly.

        :return: None
        """

        # Stop
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_STOP}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.pause.assert_called_once_with(600)
        self.mock_session.reset_mock()

        # Play
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_PLAY}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.play.assert_called_once_with()
        self.mock_session.reset_mock()

        # Pause
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_PAUSE}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.pause.assert_called_once_with(self.mock_config._POWER_OFF_DELAY_MINS * 60)
        self.mock_session.reset_mock()

        # Active device
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_ACTIVE_DEVICE}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.active.assert_called_once_with(True)
        self.mock_session.reset_mock()

        # Inactive device
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_INACTIVE_DEVICE}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.active.assert_called_once_with(False)
        self.mock_session.reset_mock()

    def test_several_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly if received in the same json.

        :return: None
        """

        # Stop, play, pause, active device, inactive device
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_STOP},
                                           {self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_PLAY},
                                           {self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_PAUSE},
                                           {self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_ACTIVE_DEVICE},
                                           {self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_INACTIVE_DEVICE}]}

        self.ev_handler.process_json_response(json)
        self.assertTrue(self.mock_session.pause.call_count == 2)
        self.assertTrue(self.mock_session.play.call_count == 1)
        self.assertTrue(self.mock_session.active.call_count == 2)

    def test_single_unknown_pb_events(self):
        """
        Tests that the event handler handles unknown playback events correctly.

        :return: None
        """

        # Unknown event type, should be ignored
        json = {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: -1}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.play.assert_not_called()
        self.mock_session.pause.assert_not_called()
        self.mock_session.active.assert_not_called()

    def test_listen_for_events_200(self):
        """
        Tests the event listening functionality in the handler in case of healthy response.

        :return: None
        """

        with patch("requests.get") as get_mock:
            self.mock_requests_get = get_mock
            self.mock_requests_get.return_value.status_code = self.mock_config._REST_SUCCESS_CODE
            self.mock_requests_get.return_value.json.return_value =\
                {self.mock_config._EVENTS: [{self.mock_config._PB_NOTIF: self.mock_config._PB_NOTIF_STOP}]}

            self.ev_handler.listen_for_events()
            self.mock_session.pause.assert_called_once_with(600)
            self.mock_session.play.assert_not_called()
            self.mock_session.active.assert_not_called()

    def test_listen_for_events_200_malformed(self):
        """
        Test behaviour of listen_for_events when responses are malformed.

        :return: None
        """

        with patch("requests.get") as get_mock:
            self.mock_requests_get = get_mock
            self.mock_requests_get.return_value.status_code = self.mock_config._REST_SUCCESS_CODE
            self.mock_requests_get.return_value.json.return_value = 123456789

            with self.assertRaises(EventError) as context:
                self.ev_handler.listen_for_events()

            self.mock_session.pause.assert_not_called()
            self.mock_session.play.assert_not_called()
            self.mock_session.active.assert_not_called()
        self.assertTrue("Response from " in str(context.exception))

    def test_listen_for_events_400(self):
        """
        Tests that the event listener works as intended in case there's a problem reaching the endpoint.

        :return: None
        """

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = self.mock_config._REST_NOT_FOUND_CODE
            with self.assertRaises(EventError) as context:
                self.ev_handler.listen_for_events()
            self.assertTrue("responded with status code" in str(context.exception))


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

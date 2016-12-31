import unittest
from unittest.mock import patch
from unittest.mock import Mock

import audio_device_controller


class SessionHandlerTest(unittest.TestCase):
    """
    Unit tests for the PlayerDeviceCoordinator class in audio_device_controller.
    """

    @staticmethod
    def match_internal_state(session, expected_state):
        """
        Help method to check that the internal state of the passed SessionHandler matches the expected one.

        :argument session: The session to be evaluated
        :argument expected_state: "Inactive, "Active", "ShortPause", "Playing", "LongPause", "Clean"
        :return: True if it's a match, False otherwise.
        """

        ret = False

        if expected_state is "Inactive":
            ret = (session._active is False and
                   session._pause_timer is None and
                   session._dev_on is False)

        elif expected_state is "ShortPause":
            ret = (session._active is True and
                   session._pause_timer is not None and
                   session._dev_on is True)

        elif expected_state is "Playing" or expected_state is "Active":
            ret = (session._active is True and
                   session._pause_timer is None and
                   session._dev_on is True)

        elif expected_state is "LongPause":
            ret = (session._active is True and
                   session._pause_timer is None and
                   session._dev_on is False)

        return ret

    def test_enter_exit(self):
        """
        Test that all the resources are correctly initialized and released.

        The device controller should be initialized and cleaned-up, pause timer should be cancelled and None-ed.
        :return: None
        """

        with patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock_timer

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl):
                mock_dev_ctrl.initialize.assert_called_once_with()

            mock_dev_ctrl.cleanup.assert_called_once_with()
            mock_dev_ctrl.reset_mock()

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
                session.active(True)
                session.play()
                session.pause(10)

            mock_dev_ctrl.standby.assert_not_called()
            mock_dev_ctrl.cleanup.assert_called_once_with()
            mock_timer.cancel.assert_called_once_with()
            self.assertTrue(self.match_internal_state(session, "Inactive"))

    def test_player_active_prev_inactive(self):
        """
        Test active command when session was inactive.

        power_on() shall be invoked.
        :return: None
        """

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
            session.active(True)
            session._send_standby()
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

        from audio_device_controller.core import AudioDeviceController
        mock_dev_ctrl = Mock(spec=AudioDeviceController)

        with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)

                mock_timer.start.called_once_with_args(10, session._send_standby)
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
                session.active(True)
                session.pause(10)

                mock_timer.start.called_once_with_args(10, session._send_standby())
                mock_dev_ctrl.power_on.not_called()
                mock_dev_ctrl.standby.not_called()

                # Timer goes off
                session._send_standby()
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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

            from audio_device_controller.core import AudioDeviceController
            mock_dev_ctrl = Mock(spec=AudioDeviceController)

            with audio_device_controller.core.Session(mock_dev_ctrl) as session:
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
            from audio_device_controller.core import AudioDeviceControllerCec

            self.controller = AudioDeviceControllerCec()
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
        from audio_device_controller.core import CecError
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
        from audio_device_controller.core import CecError
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
            from audio_device_controller.core import AudioDeviceControllerCec
            from audio_device_controller.core import CecError

            mock_popen.side_effect = OSError()

            with self.assertRaises(CecError) as context:
                controller = AudioDeviceControllerCec()
                controller.initialize()
            self.assertTrue("cec-client not found." in str(context.exception))

    def test_initialize_no_audio(self):
        """
        Test when there's no audio device connected to the hdmi bus.

        :return: None
        """
        with patch("subprocess.Popen", spec=True) as mock_popen:
            # Control the cec-client is invoked properly, audio device searched and found.
            from audio_device_controller.core import AudioDeviceControllerCec
            from audio_device_controller.core import CecError

            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("", "")

            with self.assertRaises(CecError) as context:
                controller = AudioDeviceControllerCec()
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
            from audio_device_controller.core import AudioDeviceControllerCec

            from audio_device_controller.core import CecError
            with self.assertRaises(CecError) as context:
                self.controller = AudioDeviceControllerCec()
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

        from audio_device_controller.core import AudioDeviceControllerCec

        # If something is wrong an exception will be raised...
        controller = AudioDeviceControllerCec()
        controller.cleanup()

    @staticmethod
    def test_initialize_twice():
        """
        Test that initialization of an already-initialized controller doesn't do anything.

        :return: None
        """

        from audio_device_controller.core import AudioDeviceControllerCec

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            with AudioDeviceControllerCec() as controller:
                # Control the cec-client is invoked properly, audio device searched and found
                import subprocess
                mock_popen.assert_called_once_with(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)
                mock_popen.reset_mock()

                # Second (not needed) initialization.
                controller.initialize()
                mock_popen.assert_not_called()
                mock_popen.communicate.assert_not_called()

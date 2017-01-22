import unittest
from unittest.mock import patch, Mock
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
                self.assertTrue(mock_timer.cancel.call_count is 0)
                self.assertTrue(mock_timer.start.call_count is 0)
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

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def setUp(self, mock_adapter, mock_config):
        """
        Boilerplate code to initialize the controller.

        :return: None
        """

        mock_config.return_value = mock_config
        self.mock_lib = Mock()
        mock_adapter.Create.return_value = self.mock_lib
        self.mock_lib.DetectAdapters.return_value = [Mock()]
        self.mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        self.mock_lib.Open.return_value = True
        self.mock_lib.GetDeviceOSDName.return_value = "Audio System"
        self.mock_lib.PollDevice.return_value = True

        from audio_device_controller.core import AudioDeviceControllerCec
        self.controller = AudioDeviceControllerCec()
        self.controller.initialize()

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

        self.controller.power_on()
        self.mock_lib.AudioEnable.assert_called_once_with(True)

    @patch("cec.ICECAdapter")
    def test_standby(self, mock_lib):
        """
        Test single command standby.

        :return: None
        """

        self.controller.standby()
        self.mock_lib.StandbyDevices.assert_called_once_with()


class DeviceControllerInitCleanupTest(unittest.TestCase):
    """
    Test class to test basic initialization and cleanup.
    """

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_initialize_OK(self, mock_adapter, mock_config):
        """
        Boilerplate code to initialize the controller.

        :return: None
        """

        mock_config.return_value = mock_config
        mock_lib = Mock()

        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = True

        # Control the cec-client is invoked properly, audio device searched and found
        from audio_device_controller.core import AudioDeviceControllerCec

        self.controller = AudioDeviceControllerCec()
        self.controller.initialize()

        import cec
        self.assertTrue(mock_config.strDeviceName is "audiodevctrl")
        self.assertTrue(mock_config.cActivateSource is 0)
        mock_config.deviceTypes.Add.assert_called_once_with(cec.CEC_DEVICE_TYPE_PLAYBACK_DEVICE)
        self.assertTrue(mock_config.clientVersion is cec.LIBCEC_VERSION_CURRENT)

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_initialize_OK(self, mock_adapter, mock_config):
        """
        Boilerplate code to initialize the controller.

        :return: None
        """

        mock_config.return_value = mock_config
        mock_lib = Mock()

        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = True

        # Control the cec-client is invoked properly, audio device searched and found
        from audio_device_controller.core import AudioDeviceControllerCec

        self.controller = AudioDeviceControllerCec()
        self.controller.initialize()

        import cec
        self.assertTrue(mock_config.strDeviceName is "audiodevctrl")
        self.assertTrue(mock_config.cActivateSource is 0)
        mock_config.deviceTypes.Add.assert_called_once_with(cec.CEC_DEVICE_TYPE_PLAYBACK_DEVICE)
        self.assertTrue(mock_config.clientVersion is cec.LIBCEC_VERSION_CURRENT)

        mock_adapter.Create.assert_called_once_with(mock_config)
        mock_lib.Open.assert_called_once_with(mock_lib.DetectAdapters.return_value[0].strComName)

        mock_lib.PollDevice.assert_called_once_with(cec.CECDEVICE_AUDIOSYSTEM)

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_initialize_no_cec(self, mock_adapter, mock_config):
        """
        Test when the initialization fails due to non-existing cec controller.

        :return: None
        """

        mock_config.return_value = mock_config
        mock_lib = Mock()

        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [None]
    
        # Adapter is not present.
        from audio_device_controller.core import AudioDeviceControllerCec, CecError
        with self.assertRaises(CecError) as context:
            self.controller = AudioDeviceControllerCec()
            self.controller.initialize()

            mock_adapter.Create.assert_called_once_with(mock_config)
            mock_lib.Open.assert_not_called()
            mock_lib.IsPresentDevice.assert_not_called()
        self.assertTrue("CEC adapter not found" in str(context.exception))

        # Opening the adapter gives an error.
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = False

        from audio_device_controller.core import AudioDeviceControllerCec, CecError
        with self.assertRaises(CecError) as context:
            self.controller.initialize()

            mock_adapter.Create.assert_called_once_with(mock_config)
            mock_lib.Open.assert_called_once_with(mock_lib.DetectAdapters.return_value[0].strComName)
            mock_lib.IsPresentDevice.assert_not_called()
        self.assertTrue("Could not open CEC adapter" in str(context.exception))

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_initialize_no_audio(self, mock_adapter, mock_config):
        """
        Test when there's no audio device connected to the hdmi bus.

        :return: None
        """

        mock_config.return_value = mock_config
        mock_lib = Mock()

        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = False

        from audio_device_controller.core import AudioDeviceControllerCec, CecError
        with self.assertRaises(CecError) as context:
            self.controller = AudioDeviceControllerCec()
            self.controller.initialize()
            
            import cec
            mock_adapter.Create.assert_called_once_with(mock_config)
            mock_lib.Open.assert_called_once_with(mock_lib.DetectAdapters.return_value[0])
            mock_lib.IsPresentDevice.assert_called_once_with(cec.CECDEVICE_AUDIOSYSTEM)
        self.assertTrue("cec-client does not find audio device" in str(context.exception))

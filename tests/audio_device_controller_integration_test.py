import unittest
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import call


class SystemTestCore(unittest.TestCase):
    """
    Integration tests for audio_device_controller.
    """

    @staticmethod
    def test_play():

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            from audio_device_controller.core import AudioDeviceControllerCec
            from audio_device_controller.core import Session

            with Session(AudioDeviceControllerCec()) as session:
                # Control the cec-client is invoked properly, audio device searched and found
                import subprocess
                mock_popen.assert_called_once_with(["cec-client"],
                                                   stdin=subprocess.PIPE,
                                                   stdout=subprocess.PIPE)
                mock_popen.communicate.assert_called_once_with(input="lad", timeout=15)
                mock_popen.reset_mock()

                # Session is not yet active, play should have no effect.
                session.play()
                mock_popen.communicate.assert_not_called()

                session.active(True)
                session.play()
                mock_popen.communicate.assert_called_once_with(input="on 5", timeout=15)

    @staticmethod
    def test_several_events():

        from audio_device_controller.events import ConfigOptions
        from audio_device_controller.events import EventHandler
        from audio_device_controller.core import AudioDeviceControllerCec
        from audio_device_controller.core import Session

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            with patch("requests.get") as get_mock:
                config = ConfigOptions()
                event_handler = EventHandler(Session(AudioDeviceControllerCec()), config)

                get_mock.return_value.status_code = config.rest_success_code
                get_mock.return_value.json.return_value = {
                    config.events: [{config.pb_notif: config.pb_notif_active_device},
                                    {config.pb_notif: config.pb_notif_play},
                                    {config.pb_notif: config.pb_notif_inactive_device}]}

                event_handler.listen_for_events()

                calls = [call(input="lad", timeout=15),
                         call(input="on 5", timeout=15),
                         call(input="standby 5", timeout=15)]

                mock_popen.communicate.assert_has_calls(calls)

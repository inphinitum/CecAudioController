import unittest
import sys
from unittest.mock import patch
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

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-power_on", "--debug"]
            audiodevcontroller.entry()

            import subprocess

            mock_popen.assert_called_once_with(["cec-client"],
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE)
            calls = [call(input='lad', timeout=15), call(input='on 5', timeout=15)]
            mock_popen.communicate.assert_has_calls(calls)

    @staticmethod
    def test_standby():
        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-standby", "--debug"]
            audiodevcontroller.entry()

            import subprocess

            mock_popen.assert_called_once_with(["cec-client"],
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE)
            calls = [call(input='lad', timeout=15), call(input='standby 5', timeout=15)]
            mock_popen.communicate.assert_has_calls(calls)

    @staticmethod
    def test_several_events():

        from audio_device_controller.events import ConfigOptions

        with patch("subprocess.Popen", spec=True) as mock_popen:
            mock_popen.return_value = mock_popen
            mock_popen.communicate.return_value = ("logical address 5", "")

            with patch("requests.get") as get_mock:
                config = ConfigOptions()
                config.read_from_file()

                # Events: active device, play, inactive device.
                get_mock.return_value.status_code = config.rest_success_code
                get_mock.return_value.json.side_effect = [
                    {config.events: [{config.pb_notif: config.pb_notif_active_device},
                                     {config.pb_notif: config.pb_notif_play},
                                     {config.pb_notif: config.pb_notif_inactive_device}]},
                    {""}]

                # Arguments for the entrypoint
                from audio_device_controller import audiodevcontroller

                sys.argv[1:] = ["-event_listener", "-event_timeout=1"]
                audiodevcontroller.entry()

                calls = [call(input="lad", timeout=15),
                         call(input="on 5", timeout=15),
                         call(input="standby 5", timeout=15)]
                mock_popen.communicate.assert_has_calls(calls)

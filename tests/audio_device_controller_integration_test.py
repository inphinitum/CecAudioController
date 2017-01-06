import unittest
import sys
from unittest.mock import patch
from unittest.mock import call


class SystemTestCore(unittest.TestCase):
    """
    Integration tests for audio_device_controller.
    """

    @staticmethod
    def assert_check_output(mock_subp, command):
        """
        Auxiliary method.
        :param mock_subp: Mock object for subprocess
        :param command: Input bytes literal to be sent to check_output
        :return: None
        """

        mock_subp.assert_called_once_with(
            ["cec-client", "-t", "p", "-s", "-d", "1"], input=command, timeout=30)

    @staticmethod
    def test_play():

        with patch("subprocess.check_output", spec=True) as mock_subp:
            mock_subp.return_value = b"device 5 is active"

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-power_on", "--debug"]
            audiodevcontroller.entry()

            calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"at a", timeout=30),
                     call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"tx 45:70:45:00", timeout=30)]
            mock_subp.assert_has_calls(calls)

    @staticmethod
    def test_standby():
        with patch("subprocess.check_output", spec=True) as mock_subp:
            mock_subp.return_value = b"device 5 is active"

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-standby", "--debug"]
            audiodevcontroller.entry()

            calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"at a", timeout=30),
                     call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"standby 5", timeout=30)]
            mock_subp.assert_has_calls(calls)

    @staticmethod
    def test_several_events():

        from audio_device_controller.events import ConfigOptions

        with patch("subprocess.check_output", spec=True) as mock_subp:
            mock_subp.return_value = b"device 5 is active"

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

                sys.argv[1:] = ["-event_listener", "-event_timeout=1", "--debug"]
                audiodevcontroller.entry()

                calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"at a", timeout=30),
                         call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"tx 45:70:45:00", timeout=30),
                         call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"standby 5", timeout=30)]
                mock_subp.assert_has_calls(calls)

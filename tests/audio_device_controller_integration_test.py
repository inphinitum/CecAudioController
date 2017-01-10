import sys
import unittest
try:
    from unittest.mock import call, patch, Mock
except ImportError:
    from mock import call, patch, Mock


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

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_play(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = ["adapter"]
        mock_lib.Open.return_value = True

        with patch("subprocess.check_output", spec=True) as mock_subp:

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-power_on", "--debug"]
            audiodevcontroller.entry()

            import cec

            mock_lib.PollDevice.assert_called_with(cec.CECDEVICE_AUDIOSYSTEM)
            calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"tx 45:70:45:00", timeout=30)]
            mock_subp.assert_has_calls(calls)

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_standby(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = ["adapter"]
        mock_lib.Open.return_value = True

        with patch("subprocess.check_output", spec=True) as mock_subp:

            # Arguments for the entrypoint
            from audio_device_controller import audiodevcontroller

            sys.argv[1:] = ["-standby", "--debug"]
            audiodevcontroller.entry()

            calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"standby 5", timeout=30)]
            mock_subp.assert_has_calls(calls)

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_several_events(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = ["adapter"]
        mock_lib.Open.return_value = True

        from audio_device_controller.events import ConfigOptions

        with patch("subprocess.check_output", spec=True) as mock_subp:

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

                calls = [call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"tx 45:70:45:00", timeout=30),
                         call(["cec-client", "-t", "p", "-s", "-d", "1"], input=b"standby 5", timeout=30)]
                mock_subp.assert_has_calls(calls)

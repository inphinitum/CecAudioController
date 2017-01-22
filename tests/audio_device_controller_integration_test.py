import sys
import unittest
from unittest.mock import patch, Mock


class SystemTestCore(unittest.TestCase):
    """
    Integration tests for audio_device_controller.
    """
    
    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_play(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = True

        # Arguments for the entrypoint
        from audio_device_controller import audiodevcontroller

        sys.argv[1:] = ["-power_on", "--debug"]
        audiodevcontroller.entry()

        import cec
        mock_lib.PollDevice.assert_called_with(cec.CECDEVICE_AUDIOSYSTEM)
        mock_lib.AudioEnable.assert_called_once_with(True)

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_standby(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = True

        # Arguments for the entrypoint
        from audio_device_controller import audiodevcontroller

        sys.argv[1:] = ["-standby", "--debug"]
        audiodevcontroller.entry()

        mock_lib.StandbyDevices.assert_called_once_with()

    @patch("cec.libcec_configuration")
    @patch("cec.ICECAdapter")
    def test_several_events(self, mock_adapter, mock_config):

        mock_config.return_value = mock_config
        mock_lib = Mock()
        mock_adapter.Create.return_value = mock_lib
        mock_lib.DetectAdapters.return_value = [Mock()]
        mock_lib.DetectAdapters.return_value[0].strComName = "adapter"
        mock_lib.Open.return_value = True
        mock_lib.GetDeviceOSDName.return_value = "Audio System"
        mock_lib.PollDevice.return_value = True

        from audio_device_controller.events import ConfigOptions

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
        
            mock_lib.AudioEnable.assert_called_once_with(True)
            mock_lib.StandbyDevices.assert_called_once_with()

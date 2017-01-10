import unittest
try:
    from unittest.mock import call, patch, Mock
except ImportError:
    from mock import call, patch, Mock


class EventHandlerTest(unittest.TestCase):
    """
    Unit tests for the EventHandler class in audio_device_controller.
    """

    def setUp(self):
        """
        Initialization for test cases.

        :return: None
        """
        import audio_device_controller.events

        self.mock_session                         = Mock(spec=audio_device_controller.core.Session)
        self.mock_config                          = Mock(spec=audio_device_controller.events.ConfigOptions)
        self.mock_config.rest_url                 = "http://localhost:4444/test"
        self.mock_config.rest_success_code        = 200
        self.mock_config.rest_not_found_code      = 404
        self.mock_config.events                   = "Events"
        self.mock_config.pb_notif                 = "Notification"
        self.mock_config.pb_notif_stop            = 0
        self.mock_config.pb_notif_play            = 1
        self.mock_config.pb_notif_pause           = 2
        self.mock_config.pb_notif_active_device   = 3
        self.mock_config.pb_notif_inactive_device = 4
        self.mock_config.power_off_delay_mins     = 10

        self.ev_handler = audio_device_controller.events.EventHandler(self.mock_session, self.mock_config)
        self.mock_session.active(True)
        self.mock_session.reset_mock()

    def tearDown(self):
        self.mock_session.cleanup()

    def test_not_json(self):
        """
        Tests the case when the response cannot be parsed as json.

        :return: None
        """
        import audio_device_controller.events

        with self.assertRaises(audio_device_controller.events.EventError) as context:
            response = "0123456789"
            self.ev_handler.process_json_response(response)
        self.assertTrue("Response malformed" in str(context.exception))

    def test_incorrect_response_format(self):
        """
        Tests that the event handler processes json responses correctly.

        Correct single event:    {"Events":[{"Notification": 1}]}
        Correct multiple events: {"Events":[{"Notification": 1}, {"Notification": 0}, {"Notification": 4}]}

        :return: None
        """
        import audio_device_controller.events

        # EVENTS top element not present
        json = {"Ev": [{"Notif": 0}]}

        with self.assertRaises(audio_device_controller.events.EventError) as context:
            self.ev_handler.process_json_response(json)
        self.assertTrue("Response malformed" in str(context.exception))
        self.assertTrue(self.mock_session.play.call_count is 0)
        self.assertTrue(self.mock_session.pause.call_count is 0)
        self.assertTrue(self.mock_session.active.call_count is 0)

    def test_not_recognised_events(self):
        """
        Test behaviour when JSON is correctly formed but events are not recognised.

        :return: None
        """

        # EVENTS top element not present
        json = {"Events": [{"Notif": 0}]}

        self.ev_handler.process_json_response(json)
        self.assertTrue(self.mock_session.play.call_count is 0)
        self.assertTrue(self.mock_session.pause.call_count is 0)
        self.assertTrue(self.mock_session.active.call_count is 0)

    def test_single_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly.

        :return: None
        """

        # Stop
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_stop}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.pause.assert_called_once_with(600)
        self.mock_session.reset_mock()

        # Play
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_play}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.play.assert_called_once_with()
        self.mock_session.reset_mock()

        # Pause
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_pause}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.pause.assert_called_once_with(self.mock_config.power_off_delay_mins * 60)
        self.mock_session.reset_mock()

        # Active device
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_active_device}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.active.assert_called_once_with(True)
        self.mock_session.reset_mock()

        # Inactive device
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_inactive_device}]}
        self.ev_handler.process_json_response(json)
        self.mock_session.active.assert_called_once_with(False)
        self.mock_session.reset_mock()

    def test_several_known_pb_events(self):
        """
        Tests that the event handler processes known playback events correctly if received in the same json.

        :return: None
        """

        # Stop, play, pause, active device, inactive device
        json = {self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_stop},
                                          {self.mock_config.pb_notif: self.mock_config.pb_notif_play},
                                          {self.mock_config.pb_notif: self.mock_config.pb_notif_pause},
                                          {self.mock_config.pb_notif: self.mock_config.pb_notif_active_device},
                                          {self.mock_config.pb_notif: self.mock_config.pb_notif_inactive_device}]}

        self.ev_handler.process_json_response(json)
        self.assertTrue(self.mock_session.pause.call_count is 2)
        self.assertTrue(self.mock_session.play.call_count is 1)
        self.assertTrue(self.mock_session.active.call_count is 2)

    def test_single_unknown_pb_events(self):
        """
        Tests that the event handler handles unknown playback events correctly.

        :return: None
        """

        # Unknown event type, should be ignored
        json = {self.mock_config.events: [{self.mock_config.pb_notif: -1}]}
        self.ev_handler.process_json_response(json)
        self.assertTrue(self.mock_session.play.call_count is 0)
        self.assertTrue(self.mock_session.pause.call_count is 0)
        self.assertTrue(self.mock_session.active.call_count is 0)

    def test_listen_for_events_200(self):
        """
        Tests the event listening functionality in the handler in case of healthy response.

        :return: None
        """

        with patch("requests.get") as get_mock:
            self.mock_requests_get = get_mock
            self.mock_requests_get.return_value.status_code = self.mock_config.rest_success_code
            self.mock_requests_get.return_value.json.return_value = {
                self.mock_config.events: [{self.mock_config.pb_notif: self.mock_config.pb_notif_stop}]}

            self.ev_handler.listen_for_events(-1)
            self.mock_session.pause.assert_called_once_with(600)
            self.assertTrue(self.mock_session.play.call_count is 0)
            self.assertTrue(self.mock_session.active.call_count is 0)

    def test_listen_for_events_200_malformed(self):
        """
        Test behaviour of listen_for_events when responses are malformed.

        :return: None
        """
        import audio_device_controller.events

        with patch("requests.get") as get_mock:
            self.mock_requests_get = get_mock
            self.mock_requests_get.return_value.status_code = self.mock_config.rest_success_code
            self.mock_requests_get.return_value.json.return_value = 123456789

            with self.assertRaises(audio_device_controller.events.EventError) as context:
                self.ev_handler.listen_for_events(-1)

                self.assertTrue(self.mock_session.pause.call_count is 0)
                self.assertTrue(self.mock_session.play.call_count is 0)
                self.assertTrue(self.mock_session.active.call_count is 0)
        self.assertTrue(self.mock_config.rest_url in str(context.exception))

    def test_listen_for_events_timeout(self):
        """
        Test behaviour of listen_for_events on request timeout.

        :return:
        """

        import audio_device_controller.events

        with patch("requests.get") as get_mock:

            from requests.exceptions import Timeout
            self.mock_requests_get = get_mock
            self.mock_requests_get.side_effect = Timeout()

            with self.assertRaises(audio_device_controller.events.EventError):
                self.ev_handler.listen_for_events(30)

                self.assertTrue(self.mock_session.pause.call_count is 0)
                self.assertTrue(self.mock_session.play.call_count is 0)
                self.assertTrue(self.mock_session.active.call_count is 0)

    def test_listen_for_events_400(self):
        """
        Tests that the event listener works as intended in case there's a problem reaching the endpoint.

        :return: None
        """
        import audio_device_controller.events

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = self.mock_config.rest_not_found_code
            with self.assertRaises(audio_device_controller.events.EventError) as context:
                self.ev_handler.listen_for_events(-1)
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
        import audio_device_controller.events

        self.config_options = audio_device_controller.events.ConfigOptions()

    def test_read_from_file(self):
        """
        Test that all the elements that should be read are read properly from config.ini

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
            self.assertTrue(mock_parser.return_value.read.call_count is 1)

            # Parser has been queried about the right things.
            calls = [call("EventServer", "rest_url", fallback=""),
                     call("MediaFormat", "events", fallback=""),
                     call("MediaFormat", "pb_notif", fallback="")]
            mock_parser.return_value.get.assert_has_calls(calls)

            calls = [call("MediaFormat", "pb_notif_stop", fallback=-1),
                     call("MediaFormat", "pb_notif_play", fallback=-1),
                     call("MediaFormat", "pb_notif_pause", fallback=-1),
                     call("MediaFormat", "pb_notif_active_device", fallback=-1),
                     call("MediaFormat", "pb_notif_inactive_device", fallback=-1),
                     call("DeviceControl", "power_off_delay_mins", fallback=10)]
            mock_parser.return_value.getint.assert_has_calls(calls)

            # Stored values match the provided data.
            self.assertTrue(self.config_options.rest_url is "http://localhost:5555/ev")
            self.assertTrue(self.config_options.rest_success_code is 200)
            self.assertTrue(self.config_options.events is "Events")
            self.assertTrue(self.config_options.pb_notif is "Notification")
            self.assertTrue(self.config_options.pb_notif_stop is 0)
            self.assertTrue(self.config_options.pb_notif_play is 1)
            self.assertTrue(self.config_options.pb_notif_pause is 2)
            self.assertTrue(self.config_options.pb_notif_active_device is 3)
            self.assertTrue(self.config_options.pb_notif_inactive_device is 4)
            self.assertTrue(self.config_options.power_off_delay_mins is 10)

    def test_file_not_found(self):
        """
        Thest behaviour when config file is not found.

        :return:
        """

        with patch("configparser.ConfigParser") as mock_parser:
            mock_parser.return_value = mock_parser
            mock_parser.read.return_value = []

            with self.assertRaises(ValueError) as context:
                self.config_options.read_from_file()
            self.assertTrue("Failed to open" in str(context.exception))

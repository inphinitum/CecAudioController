import cec
import logging


class Session:
    """
    This class holds the state of the player, and invokes commands on the configured device controller
    depending on if the session is active or not, content is being played or paused.
    """

    def __init__(self, dev_controller):
        self._pause_timer    = None
        self._active         = False
        self._dev_controller = dev_controller
        self._dev_on         = False

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __str__(self):
        return "".join(
            ["Session active: ", str(self._active), ", device on: ",
             str(self._dev_on), ", timer on: ",
             str(self._pause_timer is not None)])

    def initialize(self):
        self._dev_controller.initialize()

    def cleanup(self):

        if self._pause_timer is not None:
            self._pause_timer.cancel()
            self._pause_timer = None

        self._dev_controller.cleanup()
        self._dev_on = False

        self._active = False

    def active(self, new_active):
        """
        Sets the session to active.

        If the session was inactive it invokes power_on on the device controller.
        :param new_active: New session active state. True or False.
        :return: None
        """

        logging.debug("active() - " + str(self))

        if self._active is False and new_active is True:
            self._dev_controller.power_on()
            self._dev_on = True

        elif self._active is True and new_active is False:
            self._send_standby()

        self._active = new_active

    def play(self):
        """
        Session is now playing content.

        Only does something if the session is active and the device powered off. If the session was paused,
        the timer is cancelled.
        :return: None
        """

        logging.debug("play() - " + str(self))

        if self._active:
            if self._pause_timer is not None:
                self._pause_timer.cancel()
                self._pause_timer = None

            if self._dev_on is False:
                self._dev_controller.power_on()
                self._dev_on = True

    def pause(self, seconds):
        """
        Session is now paused.

        Only does something if the session is active and the device powered on. If the session was paused,
        the command is ignored.
        :argument seconds: Number of seconds to wait until standby.
        :return: None
        """

        logging.debug("pause() - " + str(self))

        if self._active:
            from threading import Timer
            if self._pause_timer is None:
                self._pause_timer = Timer(seconds, self._send_standby)
                self._pause_timer.start()

    def _send_standby(self):
        """
        Callback for the timer started on pause().

        :return: None
        """

        if self._active and self._dev_on:
            self._dev_controller.standby()
            self._dev_on = False

        if self._pause_timer:
            self._pause_timer.cancel()
            self._pause_timer = None


class CecError(Exception):
    """Exception class for Cec errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


class AudioDeviceController:
    """
    Base class for device controllers.
    """

    def __init__(self):
        """
        Default constructor.
        """
        pass

    def __enter__(self):
        """
        Initializes the controller.

        :return: self
        """
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up upon destruction.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return: None
        """
        self.cleanup()

    def initialize(self):
        """
        Base method for initializing the controller.

        :return: None
        """

        logging.info("Initializing audio device controller...")

    def cleanup(self):
        """
        Base method for cleaning up the object. Cancels any ongoing timer.

        :return: None
        """

        logging.info("Shutting down audio device controller...")

    def power_on(self):
        """
        Make sure an pending delayed_standby is cancelled.

        :return: None
        """

        logging.info("Sending power on command to audio device...")

    def select_source(self):
        """
        Sets this device active source in the audio device.

        :return: None
        """

        logging.info("Sending active source to audio device...")

    def standby(self):
        """
        Make sure any pending delayed_standby is cancelled.

        :return: None
        """

        logging.info("Sending standby command to audio device...")


class AudioDeviceControllerCec(AudioDeviceController):
    """
    Controller of devices that are cec-compatible.
    """

    def __init__(self):
        super(AudioDeviceController, self).__init__()

        self.cec_config = None
        self.cec_lib = None

    def initialize(self):
        """
        Makes sure everything is initialized to control the audio device via CEC.

        Raises:
            CecError -- if the cec-client is not found in the system.
        """
        super().initialize()

        self.cec_config = cec.libcec_configuration()
        self.cec_config.strDeviceName = "audiodevctrl"
        self.cec_config.cActivateSource = 0
        self.cec_config.deviceTypes.Add(cec.CEC_DEVICE_TYPE_PLAYBACK_DEVICE)
        self.cec_config.clientVersion = cec.LIBCEC_VERSION_CURRENT

        self.cec_lib = cec.ICECAdapter.Create(self.cec_config)

        adapter = self.cec_lib.DetectAdapters()[0]

        if adapter is None:
            raise CecError("CEC adapter not found.")
        elif self.cec_lib.Open(adapter) is not True:
            raise CecError("Could not open CEC adapter.")

        if self.cec_lib.PollDevice(cec.CECDEVICE_AUDIOSYSTEM) is False:
            raise CecError("cec-client does not find audio device.")

    def cleanup(self):
        """
        Base method for cleaning up the object. Cancels any ongoing timer.

        :return: None
        """
        super().cleanup()

    def power_on(self):
        """
        Power on the audio device.

        Raises:
             CecError -- in case cec-client is unresponsive.

        :return: None
        """

        super().power_on()

        # command 45:70:45:00
        # From logical address 4 (player) to 5 (audio)
        # System audio mode request opcode: 0x70
        # Physical address of source to be used: 4.5.0.0
        self.__cec_command(b"tx 45:70:45:00")

    def select_source(self):
        """
        Sets the active source in the audio device as this device.

        Raises:
             CecError -- in case cec-client is unresponsive.

        :return: None
        """

        super().select_source()

        # command 45:70:45:00
        # From logical address 4 (player) to 5 (audio)
        # System audio mode request opcode: 0x70
        # Physical address of source to be used: 4.5.0.0
        self.__cec_command(b"tx 45:70:45:00")

    def standby(self):
        """
        Put the audio device on standby.

        Raises:
            CecError -- in case cec-client is unresponsive.

        :return: None
        """

        super().standby()
        self.__cec_command(b"standby 5")

    @staticmethod
    def __cec_command(command):
        """
        Sends the given command to the cec process (Popen).

        Raises:
            CecError -- in case cec-client is unresponsive.
        """
        import subprocess

        try:
            return subprocess.check_output(["cec-client", "-t", "p", "-s", "-d", "1"], input=command, timeout=30)

        except OSError:
            raise CecError("cec-client not found.")
        except subprocess.TimeoutExpired:
            raise CecError("cec-client unresponsive.")

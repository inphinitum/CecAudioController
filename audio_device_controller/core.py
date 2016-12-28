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

    def initialize(self):
        self._dev_controller.initialize()

    def cleanup(self):

        if self._pause_timer is not None:
            self._pause_timer.cancel()
            self._pause_timer = None

        self._dev_controller.standby()
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

        if self._active is False and new_active is True:
            self._dev_controller.power_on()
            self._dev_on = True

        elif self._active is True and new_active is False:
            # Cancel previous _pause_timer first
            if self._pause_timer is not None:
                self._pause_timer.cancel()
                self._pause_timer = None

            self._dev_controller.standby()
            self._dev_on = False

        self._active = new_active

    def play(self):
        """
        Session is now playing content.

        Only does something if the session is active and the device powered off. If the session was paused,
        the timer is cancelled.
        :return: None
        """

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

        if self._active:
            from threading import Timer
            if self._pause_timer is None:
                self._pause_timer = Timer(seconds, self._callback_pause_timeout)
                self._pause_timer.start()

    def _callback_pause_timeout(self):
        """
        Callback for the timer started on pause().

        :return: None
        """

        if self._active and self._dev_on:
            self._dev_controller.standby()
            self._dev_on = False
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
        super().__init__()

        self._AUDIO_LOGICAL_ADDRESS = 5
        self._cec_process           = None
        self._cec_lib               = None

    def initialize(self):
        """
        Makes sure everything is initialized to control the audio device via CEC.

        Raises:
            CecError -- if the cec-client is not found in the system.
        """
        super().initialize()

        if self._cec_process is None:
            try:
                import subprocess
                self._cec_process = subprocess.Popen(["cec-client"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                output = self.__cec_command("lad")

                if "logical address 5" not in output:
                    raise CecError("cec-client does not find audio device.")

            except OSError:
                raise CecError("cec-client not found.")

    def cleanup(self):
        """
        Clean up all spawned threads.

        :return: None
        """
        super().cleanup()

        # Stop the thread for the cec-tool
        if self._cec_process is not None and callable(getattr(self._cec_process, "terminate")):
            self._cec_process.terminate()
            self._cec_process = None

    def power_on(self):
        """
        Power on the audio device.

        Raises:
             CecError -- in case cec-client is unresponsive.

        :return: None
        """

        super().power_on()

        self.__cec_command("on 5")


    def standby(self):
        """
        Put the audio device on standby.

        Raises:
            CecError -- in case cec-client is unresponsive.

        :return: None
        """

        super().standby()

        self.__cec_command("standby 5")

    def __cec_command(self, command):
        """
        Sends the given command to the cec process (Popen).

        Raises:
            CecError -- in case cec-client is unresponsive.
        """
        import subprocess

        try:
            output, error = self._cec_process.communicate(input=command, timeout=15)

        except subprocess.TimeoutExpired:
            self._cec_process.terminate()
            raise CecError("cec-client unresponsive, terminated.")

        return output, error

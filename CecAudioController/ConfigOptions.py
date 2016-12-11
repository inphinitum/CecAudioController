# class ConfigOptions
#
# Handles configuration options, including reading from disk (config.ini)
class ConfigOptions:

    # Definitions
    REST_URL                 = ""
    REST_SUCCESS_CODE        = 200      # Standard HTTP success response code
    EVENTS                   = ""
    PB_NOTIF                 = ""
    PB_NOTIF_STOP            = -1
    PB_NOTIF_PLAY            = -1
    PB_NOTIF_PAUSE           = -1
    PB_NOTIF_ACTIVE_DEVICE   = -1
    PB_NOTIF_INACTIVE_DEVICE = -1
    POWER_OFF_DELAY_MINS     = 10

    # read_from_file()
    #
    # Reads from config.ini in the same directory the necessary configuration params.
    # File structure (and example values):
    #     [EventServer]
    #     rest_url=http://localhost:8080/endpoint
    #
    #     [MediaFormat]
    #     events = "Events"
    #     pb_notif = "Notification"
    #     pb_notif_stop = 0
    #     pb_notif_play = 1
    #     pb_notif_pause = 2
    #     pb_notif_active_device = 3
    #     pb_notif_inactive_device = 4
    def read_from_file(self):
        config = ConfigParser.SafeConfigParser()
        config.optionxform = str
        config.read("config.ini")

        # [EventServer]
        if config.has_option("EventServer", "rest_url"):
            self.REST_URL = config.get("EventServer", "rest_url")

        # [MediaFormat]
        if config.has_option("MediaFormat", "events"):
            self.EVENTS = config.get("MediaFormat", "events")
        if config.has_option("MediaFormat", "pb_notif"):
            self.PB_NOTIF = config.get("MediaFormat", "pb_notif")
        if config.has_option("MediaFormat", "pb_notif_stop"):
            self.PB_NOTIF_STOP = config.getint("MediaFormat", "pb_notif_stop")
        if config.has_option("MediaFormat", "pb_notif_play"):
            self.PB_NOTIF_PLAY = config.getint("MediaFormat", "pb_notif_play")
        if config.has_option("MediaFormat", "pb_notif_pause"):
            self.PB_NOTIF_PAUSE = config.getint("MediaFormat", "pb_notif_pause")
        if config.has_option("MediaFormat", "pb_notif_pause"):
            self.PB_NOTIF_ACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_active_device")
        if config.has_option("MediaFormat", "pb_notif_inactive_device"):
            self.PB_NOTIF_INACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_inactive_device")

        # [DeviceControl]
        if config.has_option("DeviceControl", "power_off_delay_mins"):
            self.POWER_OFF_DELAY_MINS = config.getint("DeviceControl", "power_off_delay_mins")

    # to_string()
    #
    # Returns a string with the current configuration.
    def to_string(self):
        ret = "Configuration options\n======================="
        ret += "\nURL:                 " + self.REST_URL
        ret += "\nEvents:              " + self.EVENTS
        ret += "\nPB notification:     " + self.PB_NOTIF
        ret += "\nPB stop:             " + str(self.PB_NOTIF_STOP)
        ret += "\nPB play:             " + str(self.PB_NOTIF_PLAY)
        ret += "\nPB pause:            " + str(self.PB_NOTIF_PAUSE)
        ret += "\nPB active device:    " + str(self.PB_NOTIF_ACTIVE_DEVICE)
    config.read("config.ini")

    # [EventServer]
    if config.has_option("EventServer", "rest_url"):
        self.REST_URL = config.get("EventServer", "rest_url")

    # [MediaFormat]
    if config.has_option("MediaFormat", "events"):
        self.EVENTS = config.get("MediaFormat", "events")
    if config.has_option("MediaFormat", "pb_notif"):
        self.PB_NOTIF = config.get("MediaFormat", "pb_notif")
    if config.has_option("MediaFormat", "pb_notif_stop"):
        self.PB_NOTIF_STOP = config.getint("MediaFormat", "pb_notif_stop")
    if config.has_option("MediaFormat", "pb_notif_play"):
        self.PB_NOTIF_PLAY = config.getint("MediaFormat", "pb_notif_play")
    if config.has_option("MediaFormat", "pb_notif_pause"):
        self.PB_NOTIF_PAUSE = config.getint("MediaFormat", "pb_notif_pause")
    if config.has_option("MediaFormat", "pb_notif_pause"):
        self.PB_NOTIF_ACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_active_device")
    if config.has_option("MediaFormat", "pb_notif_inactive_device"):
        self.PB_NOTIF_INACTIVE_DEVICE = config.getint("MediaFormat", "pb_notif_inactive_device")

    # [DeviceControl]
    if config.has_option("DeviceControl", "power_off_delay_mins"):
        self.POWER_OFF_DELAY_MINS = config.getint("DeviceControl", "power_off_delay_mins")

    # to_string()
    #
    # Returns a string with the current configuration.
    def to_string(self):
        ret = "Configuration options\n======================="
        ret += "\nURL:                 " + self.REST_URL
        ret += "\nEvents:              " + self.EVENTS
        ret += "\nPB notification:     " + self.PB_NOTIF
        ret += "\nPB stop:             " + str(self.PB_NOTIF_STOP)
        ret += "\nPB play:             " + str(self.PB_NOTIF_PLAY)
        ret += "\nPB pause:            " + str(self.PB_NOTIF_PAUSE)
        ret += "\nPB active device:    " + str(self.PB_NOTIF_ACTIVE_DEVICE)
        ret += "\nPB inactive device:  " + str(self.PB_NOTIF_INACTIVE_DEVICE)
        ret += "\nSTBY delay minutes:  " + str(self.POWER_OFF_DELAY_MINS)
        ret += "\n\n"

        return ret

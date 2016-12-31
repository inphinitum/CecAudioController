import argparse
import logging


parser = argparse.ArgumentParser(description="Control an audio device via CEC.")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-power_on", action="store_const", const=True,
                   help="Power on the audio device", default=False)
group.add_argument("-standby", action="store_const", const=True,
                   help="Set the audio device to standby", default=False)
group.add_argument("-event_listener", action="store_const", const=True,
                   help="Listen for events to control the audio device", default=False)

parser.add_argument("-event_timeout", type=int, dest="event_timeout",
                    help="Timeout when listening for events in seconds", default=-1)
parser.add_argument("-comm_type", type=str, choices=["cec"],
                    help="Type of communication with the audio device (HDMI CEC, IR...)",
                    default="cec")
parser.add_argument("--debug", dest="debug", action="store_const", const=True,
                    help="Enable debugging", default=False)


def config_logging(arguments):
    if arguments.debug:
        logging.basicConfig(level="DEBUG")


def entry():
    # TODO: Capture terminate signals for proper cleanup.
    # signal.signal(signal.SIGTERM, €€€)

    arguments = parser.parse_args()
    config_logging(arguments)

    logging.info("Started")

    from .core import Session, AudioDeviceControllerCec, CecError
    from .events import EventHandler, EventError, ConfigOptions

    try:
        if arguments.power_on:
            with AudioDeviceControllerCec() as controller:
                controller.power_on()

        elif arguments.standby:
            with AudioDeviceControllerCec() as controller:
                controller.standby()

        elif arguments.event_listener:
            config = ConfigOptions()
            with EventHandler(Session(AudioDeviceControllerCec()), config) as event_handler:
                logging.info("Initialization OK, listening for events on " + config.rest_url)

                while True:
                    event_handler.listen_for_events(arguments.event_timeout)

    except (CecError, EventError) as e:
        logging.critical(e.message)

    logging.info("Exiting")

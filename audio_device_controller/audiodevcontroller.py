import argparse
import logging
import signal

import audio_device_controller.core
import audio_device_controller.events

controller = None
session = None


parser = argparse.ArgumentParser(description="Control an audio device via CEC.")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-power_on", action="store_const", const=True,
                   help="Power on the audio device", default=False)
group.add_argument("-standby", action="store_const", const=True,
                   help="Set the audio device to standby", default=False)
group.add_argument("-event_listener", action="store_const", const=True,
                   help="Listen for events to control the audio device", default=False)

parser.add_argument("-comm_type", type=str, choices=["cec"],
                    help="Type of communication with the audio device (HDMI CEC, IR...)",
                    default="cec")
parser.add_argument("--debug", dest="debug", action="store_const", const=True,
                    help="Enable debugging", default=False)


def config_logging(arguments):
    if arguments.debug:
        logging.basicConfig(level="DEBUG")


def on_exit():
    if controller is not None:
        controller.cleanup()

    if session is not None:
        session.cleanup()


def entry():
    # Capture terminate signals for proper cleanup.
    signal.signal(signal.SIGTERM, on_exit)

    arguments = parser.parse_args()
    config_logging(arguments)

    logging.info("Started")

    try:
        global controller
        controller = audio_device_controller.core.AudioDeviceControllerCec()
        controller.initialize()

        if arguments.power_on:
            controller.power_on()

        elif arguments.standby:
            controller.standby()

        else:
            global session
            session = audio_device_controller.core.Session(controller)
            session.initialize()

            # Gather configuration options
            config = audio_device_controller.events.ConfigOptions()
            config.read_from_file()

            logging.info("Initialization OK, listening for events on " + config.rest_url)
            with audio_device_controller.events.EventHandler(session, config) as ev_handler:
                while True:
                    ev_handler.listen_for_events()

    except (audio_device_controller.core.CecError, audio_device_controller.events.EventError) as e:
        logging.critical(e.message)

    on_exit()

    logging.info("Exiting")

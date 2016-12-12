# __init__.py
#
# Copyright (C) 2016 Javier Martinez <javi@flamingalah.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MECHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# This file provides a Python script to control a device via HDMI-CEC based
# on events published via http
#
# Depends on libcec <https://github.com/Pulse-Eight/libcec>
#
# Author: Javier Martinez <javi@flamingalah.net>

import argparse
from CecAudioController import ConfigOptions
from CecAudioController import DeviceController
from CecAudioController import EventHandler

if __name__ == '__main__':
    power_on = False
    standby = False
    event_listener = False

    parser = argparse.ArgumentParser(description="Control an audio device via CEC.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-power_on", action="store_false")
    group.add_argument("-standby", action="store_false")
    group.add_argument("-event_listener", action="store_false")
    arguments = parser.parse_args([])

    # Initialize CEC stuff and listen for events if OK
    controller = DeviceController()
    if controller.init_CEC():
        if arguments.power_on:
            controller.power_on()
        elif arguments.standby:
            controller.standby()
        else:
            # Gather configuration options
            config = ConfigOptions()
            config.read_from_file()

            print("Initialization OK, listening for events on " + config.REST_URL)
            EventHandler().listen_for_events()
    else:
        print("Initialization NOK, quitting...")

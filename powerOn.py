#!/usr/bin/env python2

# powerOn.py
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

import cec
from threading import Timer

# Global variables
controller = None
config     = None

# class DeviceController
#
# Controls a device via HDMI-CEC. Power on is immediate, Power off can be
# delayed (e.g. music is paused for just a moment).
class DeviceController:
    _cecConfig = cec.libcec_configuration()
    _cecLib = None
    _adapter = None
    _isPowerOn = None
    _powerOffTimer = None

    def __init__(self):
        self.set_configuration()

    # set_configuration()
    #
    # Minimum configuration of the cec library. OBS, doesn't initialize it.
    def set_configuration(self):
        self._cecConfig.strDeviceName = "PiRecCtrl"
        self._cecConfig.bActivateSource = 0
        self._cecConfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_AUDIO_SYSTEM)
        self._cecConfig.clientVersion = cec.LIBCEC_VERSION_CURRENT

    # init_CEC()
    #
    # Makes sure everything is initialized to control the audio device via CEC.
    #
    # Returns True if successful, False otherwise
    def init_CEC(self):
        return self.init_adapter() and self.init_audio_device()

    # init_adapter()
    #
    # Initializes the CEC adapter in the system if any.
    #
    # Returns True if adapter found, False otherwise.
    def init_adapter(self):
        adapter = None

        # Initialize adapter
        self._cecLib = cec.ICECAdapter.Create(self._cecConfig)
        adapters = self._cecLib.DetectAdapters()
        for ad in adapters:
            print("CEC adapter\n===========")
            print("port:     " + ad.strComName)
            print("vendor:   " + hex(ad.iVendorId))
            print("product:  " + hex(ad.iProductId))
            print("\n")
            adapter = ad.strComName

        if adapter != None:
            self._cecLib.Open(adapter)
            return True
        else:
            return False

    # init_audio_device()
    #
    # Searches for the audio device in the system.
    #
    # Returns True if the audio device was found, False otherwise.
    def init_audio_device(self):
        retVal = False

        # Connect to audio device
        devices = self._cecLib.GetActiveDevices()
        strLog = "Audio device in CEC bus\n=======================\n"
        global AUDIO_LOGICAL_ADDRESS

        if devices.IsSet(config.AUDIO_LOGICAL_ADDRESS):
            vendorId        = self._cecLib.GetDeviceVendorId(config.AUDIO_LOGICAL_ADDRESS)
            physicalAddress = self._cecLib.GetDevicePhysicalAddress(config.AUDIO_LOGICAL_ADDRESS)
            active          = self._cecLib.IsActiveSource(config.AUDIO_LOGICAL_ADDRESS)
            cecVersion      = self._cecLib.GetDeviceCecVersion(config.AUDIO_LOGICAL_ADDRESS)
            power           = self._cecLib.GetDevicePowerStatus(config.AUDIO_LOGICAL_ADDRESS)
            osdName         = self._cecLib.GetDeviceOSDName(config.AUDIO_LOGICAL_ADDRESS)
            strLog += "device #" + str(config.AUDIO_LOGICAL_ADDRESS) +":     "
            strLog += self._cecLib.LogicalAddressToString(config.AUDIO_LOGICAL_ADDRESS)  + "\n"
            strLog += "address:       " + str(physicalAddress) + "\n"
            strLog += "active source: " + str(active) + "\n"
            strLog += "vendor:        " + self._cecLib.VendorIdToString(vendorId) + "\n"
            print("CEC adapter\n===========")
            print("port:     " + ad.strComName)
            print("vendor:   " + hex(ad.iVendorId))
            print("product:  " + hex(ad.iProductId))
            print("\n")
            adapter = ad.strComName

        if adapter != None:
            self._cecLib.Open(adapter)
            return True
        else:
            return False

    # init_audio_device()
    #
    # Searches for the audio device in the system.
    #
    # Returns True if the audio device was found, False otherwise.
    def init_audio_device(self):
        retVal = False

        # Connect to audio device
        devices = self._cecLib.GetActiveDevices()
        strLog = "Audio device in CEC bus\n=======================\n"
        global AUDIO_LOGICAL_ADDRESS

        if devices.IsSet(config.AUDIO_LOGICAL_ADDRESS):
            vendorId        = self._cecLib.GetDeviceVendorId(config.AUDIO_LOGICAL_ADDRESS)
            physicalAddress = self._cecLib.GetDevicePhysicalAddress(config.AUDIO_LOGICAL_ADDRESS)
            active          = self._cecLib.IsActiveSource(config.AUDIO_LOGICAL_ADDRESS)
            cecVersion      = self._cecLib.GetDeviceCecVersion(config.AUDIO_LOGICAL_ADDRESS)
            power           = self._cecLib.GetDevicePowerStatus(config.AUDIO_LOGICAL_ADDRESS)
            osdName         = self._cecLib.GetDeviceOSDName(config.AUDIO_LOGICAL_ADDRESS)
            strLog += "device #" + str(config.AUDIO_LOGICAL_ADDRESS) +":     "
            strLog += self._cecLib.LogicalAddressToString(config.AUDIO_LOGICAL_ADDRESS)  + "\n"
            strLog += "address:       " + str(physicalAddress) + "\n"
            strLog += "active source: " + str(active) + "\n"
            strLog += "vendor:        " + self._cecLib.VendorIdToString(vendorId) + "\n"
            strLog += "CEC version:   " + self._cecLib.CecVersionToString(cecVersion) + "\n"
            strLog += "OSD name:      " + osdName + "\n"
            strLog += "power status:  " + self._cecLib.PowerStatusToString(power) + "\n\n"

            self._isPowerOn = power == "on";

            retVal = True
        else:
            strLog += "No audio device found!!!\n"

        print(strLog)

        return retVal

    # standby()
    #
    # Powers off the receiver immediately and cancels any ongoing power off
    # timer
    def standby(self):
        print("STANDBY requested")
        self._cecLib.StandbyDevices(config.AUDIO_LOGICAL_ADDRESS)
        self._isPowerOn = False

        # If there was a timer, cancel and release.
        if self._powerOffTimer:
            self._powerOffTimer.cancel()
            self._powerOffTimer = None
            strLog += "power status:  " + self._cecLib.PowerStatusToString(power) + "\n\n"

            self._isPowerOn = power == "on";

            retVal = True
        else:
            strLog += "No audio device found!!!\n"

        print(strLog)

        return retVal

    # power_on()
    #
    # Powers on the receiver immediately and cancels any ongoing power off timer
    def power_on(self):
        print("Power ON requested")
        self._cecLib.PowerOnDevices(config.AUDIO_LOGICAL_ADDRESS)
        self._isPowerOn = True

        # If there was a timer, cancel and release.
        if self._powerOffTimer:
            self._powerOffTimer.cancel()
            self._powerOffTimer = None

    # standby()
    #
    # Powers off the receiver immediately and cancels any ongoing power off
    # timer
    def standby(self):
        print("STANDBY requested")
        self._cecLib.StandbyDevices(config.AUDIO_LOGICAL_ADDRESS)
        self._isPowerOn = False

        # If there was a timer, cancel and release.
        if self._powerOffTimer:
            self._powerOffTimer.cancel()
            self._powerOffTimer = None

    # delayed_standby(seconds)
    #
    # Will put the receiver on STBY in the given number of seconds. Used for
    # temporary pauses, when switching off is annoying for the user. This
    # action will be cancelled if a power_on or power_off command is received
    # before the timer lapses.
    def delayed_standby(self, seconds):
        print("Delayed STANDBY requested")
        if self._isPowerOn:
            self._standby_timer = Timer(seconds, self.standby)
            self._standby_timer.start()

if __name__ == '__main__':
    # Initialize CEC stuff
    controller = DeviceController()
    if controller.init_CEC():
        controller.power_on()
    else:
        print("Initialization NOK, quitting...")
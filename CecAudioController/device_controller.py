# This file is part of CecAudioController.
#
# CecAudioController is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CecAudioController is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CecAudioController.  If not, see <http://www.gnu.org/licenses/>.

#
# Depends on libcec <https://github.com/Pulse-Eight/libcec>
#
# Author: Javier Martinez <javi@flamingalah.net>
# class DeviceController
#
# Controls a device via HDMI-CEC. Power on is immediate, Power off can be
# delayed (e.g. music is paused for just a moment).

import cec
from threading import Timer


class DeviceController:
    AUDIO_LOGICAL_ADDRESS = 5
    _cecConfig            = cec.libcec_configuration()
    _cecLib               = None
    _is_power_on          = None
    _standby_timer        = None
    _config_params        = None

    # __init__(self)
    #
    # Default constructor.
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
    def init_cec(self):
        return self.init_adapter() and self.init_audio_device()

    # init_adapter()
    #
    # Initializes the CEC adapter in the system if any.
    #
    # Returns True if adapter found, False otherwise.
    def init_adapter(self):
        adapter = ""

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

        if adapter != "":
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
        ret_val = False

        # Connect to audio device
        devices = self._cecLib.GetActiveDevices()
        str_log = "Audio device in CEC bus\n=======================\n"
        global AUDIO_LOGICAL_ADDRESS

        if devices.IsSet(self._config_params.AUDIO_LOGICAL_ADDRESS):
            vendorId        = self._cecLib.GetDeviceVendorId(self._config_params.AUDIO_LOGICAL_ADDRESS)
            physicalAddress = self._cecLib.GetDevicePhysicalAddress(self._config_params.AUDIO_LOGICAL_ADDRESS)
            active          = self._cecLib.IsActiveSource(self._config_params.AUDIO_LOGICAL_ADDRESS)
            cecVersion      = self._cecLib.GetDeviceCecVersion(self._config_params.AUDIO_LOGICAL_ADDRESS)
            power           = self._cecLib.GetDevicePowerStatus(self._config_params.AUDIO_LOGICAL_ADDRESS)
            osdName         = self._cecLib.GetDeviceOSDName(self._config_params.AUDIO_LOGICAL_ADDRESS)
            str_log += "device #" + str(self._config_params.AUDIO_LOGICAL_ADDRESS) + ":     "
            str_log += self._cecLib.LogicalAddressToString(self._config_params.AUDIO_LOGICAL_ADDRESS) + "\n"
            str_log += "address:       " + str(physicalAddress) + "\n"
            str_log += "active source: " + str(active) + "\n"
            str_log += "vendor:        " + self._cecLib.VendorIdToString(vendorId) + "\n"
            str_log += "CEC version:   " + self._cecLib.CecVersionToString(cecVersion) + "\n"
            str_log += "OSD name:      " + osdName + "\n"
            str_log += "power status:  " + self._cecLib.PowerStatusToString(power) + "\n\n"

            self._is_power_on = power == "on"
            ret_val = True
        else:
            str_log += "No audio device found!!!\n"

        print(str_log)
        return ret_val

    # power_on()
    #
    # Powers on the receiver immediately and cancels any ongoing power off timer
    def power_on(self):
        print("Power ON requested")
        self._cecLib.PowerOnDevices(self._config_params.AUDIO_LOGICAL_ADDRESS)
        self._is_power_on = True

        # If there was a timer, cancel and release.
        if self._standby_timer:
            self._standby_timer.cancel()
            self._standby_timer = None

    # standby()
    #
    # Powers off the receiver immediately and cancels any ongoing power off
    # timer
    def standby(self):
        print("STANDBY requested")
        self._cecLib.StandbyDevices(self._config_params.AUDIO_LOGICAL_ADDRESS)
        self._is_power_on = False

        # If there was a timer, cancel and release.
        if self._standby_timer:
            self._standby_timer.cancel()
            self._standby_timer = None

    # delayed_standby(seconds)
    #
    # Will put the receiver on STBY in the given number of seconds. Used for
    # temporary pauses, when switching off is annoying for the user. This
    # action will be cancelled if a power_on or power_off command is received
    # before the timer lapses.
    def delayed_standby(self, seconds):
        print("Delayed STANDBY requested")
        if self._is_power_on:
            self._standby_timer = Timer(seconds, self.standby)
            self._standby_timer.start()

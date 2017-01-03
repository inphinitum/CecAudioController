# audio-device-controller

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](http://www.repostatus.org/badges/1.1.0/wip.svg)](http://www.repostatus.org/#wip)
[![Build Status](https://travis-ci.org/inphinitum/audio-device-controller.svg?branch=master)](https://travis-ci.org/inphinitum/audio-device-controller)
[![codecov](https://codecov.io/gh/inphinitum/audio-device-controller/branch/master/graph/badge.svg)](https://codecov.io/gh/inphinitum/audio-device-controller)
[![Code Climate](https://codeclimate.com/github/inphinitum/audio-device-controller/badges/gpa.svg)](https://codeclimate.com/github/inphinitum/audio-device-controller)
[![License](https://img.shields.io/github/license/inphinitum/audio-device-controller.svg)](LICENSE)

Controller of audio devices via different options. Provided today:
- HDMI and CEC-compatible.

Can listen to events via a REST API, or be called with specific commands.

## Dependencies
This project depends on [libcec](https://github.com/Pulse-Eight/libcec).

## Installation for Raspbian
First you will need to install `libcec`. [Trainman419](https://github.com/trainman419) has built a custom build with Raspberry Pi support:
```
wget http://packages.namniart.com/repos/namniart.key -O - | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.namniart.com/repos/pi wheezy main" > /etc/apt/sources.list.d/libcec.list'
sudo apt-get update
sudo apt-get install python-dev build-essential libcec-dev cec-utils
```
Make sure you have `python3` and `pip` installed:
``` bash
sudo apt-get install python3
sudo apt-get install python3-pip
```
Download and install audio-device-controller:
```
wget https://github.com/inphinitum/audio-device-controller/releases/download/0.1.0-beta/audio_device_controller-0.1.0.dev0-py3-none-any.whl
pip3 install audio_device_controller-0.1.0.dev0-py3-none-any.whl
```

## Examples
Using the command line utility:
``` bash
usage: audio-dev-controller [-h] (-power_on | -standby | -event_listener)
                            [-event_timeout EVENT_TIMEOUT] [-comm_type {cec}]
                            [--debug]
```
Using the package from your code:
```python
with SessionHandler() as session:
    session.active(True)
    session.play()
```
```python
with DeviceControllerCec() as controller:
    controller.standby()
```
```python
with EventHandler(session, config) as ev_handler:
    while True:
        ev_handler.listen_for_events()
```

## Configuration file

The configuration file is only necessary when using the event_listener, and is read with the given precedence from:
  1. ./config.ini
  2. ~/.audio-device-controller/config.ini
  3. /etc/audio-device-controller/config.ini

It has the following format:
```
[EventServer]
rest_url=http://localhost:8080/endpoint

[MediaFormat]
events = "Events"
pb_notif = "Notification"
pb_notif_stop = 0
pb_notif_play = 1
pb_notif_pause = 2
pb_notif_active_device = 3
pb_notif_inactive_device = 4

[DeviceControl]
power_off_delay_mins = 10
```

`EventServer` holds info about the REST endpoint, `MediaFormat` about the REST API message format,
and `DeviceControl` about how the device should be controlled.

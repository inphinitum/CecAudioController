# cec_audio_controller

Controller of audio devices that are connected via HDMI and CEC-compatible.

Can listen to events via a REST API, or be called with specific commands.

## Examples

```python
controller = device_controller()
controller.power_on()
```
```python
controller = device_controller()
controller.standby()
```
```python
controller = device_controller()

config = config_options.ConfigOptions()
config.read_from_file()

ev_handler = event_handler.EventHandler(controller, config)
ev_handler.listen_for_events()
ev_handler.listen_for_events()
```

## Configuration file

The configuration file has the following format:
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

## audio_controller

`audio_controller` is provided as an example of how the library can be used standalone.

```bash
$ audio_controller.py -event_listener
```
```bash
$ audio_controller.py -power_on
```
```bash
$ audio_controller.py -standby
```
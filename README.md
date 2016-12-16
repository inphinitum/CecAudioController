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
controller.listen_for_events()
```

## audio_controller

`audio_controller` is provided as an example of how the library can be used standalone.

```bash
python audio_controller.py -event_listener
```
```bash
python audio_controller.py -power_on
```
```bash
python audio_controller.py -standby
```
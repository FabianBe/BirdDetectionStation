from mock import Mock  # type: ignore
import sys
import types


def query_devices(device=None):
    device_settings: dict = {
        "name": "Test audio device",
        "hostapi": 0,
        "max_input_channels": 2,
        "max_output_channels": 2,
        "default_low_input_latency": 0.00870751953125,
        "default_low_output_latency": 0.00870751953125,
        "default_high_input_latency": 0.034830078125,
        "default_high_output_latency": 0.034830078125,
        "default_samplerate": 44099.81494981215,
    }
    if device == None:
        return [device_settings]
    else:
        return device_settings


def mock_sounddevice_module():
    module_name = "sounddevice"
    sounddevice_module = types.ModuleType(module_name)
    sounddevice_module = Mock(name=module_name)
    sounddevice_module.DeviceList = []  # type: ignore
    sounddevice_module.query_devices.side_effect = query_devices  # type: ignore
    sys.modules[module_name] = sounddevice_module

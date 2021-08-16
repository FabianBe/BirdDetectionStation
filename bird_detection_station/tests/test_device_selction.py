from bird_detection.audio.device_selection import DeviceSelector


def test_get_device_list():
    device_selector = DeviceSelector()
    devices = device_selector.list_devices()
    assert len(devices) > 0


def test_set_device():
    device_selector = DeviceSelector()
    devices = device_selector.list_devices()
    device = devices[0]
    device_selector._set_device(device["name"])
    assert device_selector.is_device_selected()

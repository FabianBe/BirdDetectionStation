from serial import SerialException  # type: ignore

import bird_detection.gps.location_service

from bird_detection.gps.location_service import LocationService


class SerialStubError:
    def __init__(self, port=None, baudrate=9600, timeout=None, **kwargs):
        raise SerialException()


class SerialStub:
    def __init__(self, port=None, baudrate=9600, timeout=None, **kwargs):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def isOpen(self):
        return True

    def readline(self):
        return b"$GPGGA,123011.345,5333.887,N,01000.399,E,1,12,1.0,0.0,M,0.0,M,,*6F\r\n"


def test_is_GPS_sensor_attached(monkeypatch):
    monkeypatch.setattr(bird_detection.gps.location_service, "Serial", SerialStub)
    location_service = LocationService()
    is_GPS_sensor_atteched = location_service.is_GPS_sensor_attached()
    assert is_GPS_sensor_atteched

    monkeypatch.setattr(bird_detection.gps.location_service, "Serial", SerialStubError)
    location_service = LocationService()
    is_GPS_sensor_atteched = location_service.is_GPS_sensor_attached()
    assert not is_GPS_sensor_atteched


def test_get_valid_location(monkeypatch):
    monkeypatch.setattr(bird_detection.gps.location_service, "Serial", SerialStub)
    location_service = LocationService()
    location = location_service.get_valid_location()
    assert location.lat == "53.56478333333333"
    assert location.lon == "10.00665"

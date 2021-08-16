import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import pynmea2  # type: ignore
from serial import Serial  # type: ignore
from serial.serialutil import SerialException  # type: ignore


class Location:
    def __init__(self, lat: str, lon: str):
        self.lat = lat
        self.lon = lon


class SerialPortConfig:
    def __init__(
        self, path: str = "/dev/serial0", baud_rate: int = 9600, timeout: float = 0.5
    ):
        self.path = path
        self.baud_rate = baud_rate
        self.timeout = timeout


class LocationServiceInterface(ABC):
    @abstractmethod
    def is_GPS_sensor_attached(self) -> bool:
        """
        Validates if a GPS module is attached
        :return: true if a sensor is attached otherwise false
        """
        pass

    @abstractmethod
    def get_valid_location(self) -> Location:
        """
        Get the last known location based on the GPS sensor readings
        :return: A GPSCoordinates object which represents a geographic
        coordinate based on latitude and longitude
        """
        pass


class LocationService(LocationServiceInterface):
    NMEA_SENTENCE_GPGGA = "GPGGA"

    def __init__(
        self,
        gps_coordinates: Location = None,
        serial_port_config: SerialPortConfig = SerialPortConfig(),
        timeout: float = 0.5,
    ):
        self.gps_coordinates = gps_coordinates
        self.serial_port_config = serial_port_config
        self.timeout = timeout
        self.serial_port = self.__init_GPS_senor()

    def get_valid_location(self):
        if self.is_GPS_sensor_attached():
            new_gps_coordinates = self._try_to_read_location()
            self.gps_coordinates = (
                new_gps_coordinates
                if new_gps_coordinates is not None
                else self.gps_coordinates
            )
        else:
            logging.warning(
                "Default location value is used because no GPS-Sensor was initialized."
            )
        return self.gps_coordinates

    def is_GPS_sensor_attached(self) -> bool:
        return self.serial_port is not None and self.serial_port.isOpen()

    def __init_GPS_senor(self) -> Serial:
        serial_port = None
        try:
            serial_port = Serial(
                self.serial_port_config.path,
                self.serial_port_config.baud_rate,
                timeout=self.serial_port_config.timeout,
            )
        except (SerialException, FileNotFoundError):
            logging.warning("No GPS-Sensor detected")

        return serial_port

    def _try_to_read_location(self) -> Optional[Location]:
        valid = False
        next_timeout = time.time() + self.timeout
        new_gps_coordinates = None
        while not valid and next_timeout > time.time():
            line = self.serial_port.readline()
            coordinates = self._parseGPS(line)
            if coordinates:
                new_gps_coordinates = coordinates
                valid = True
        return new_gps_coordinates

    def _parseGPS(self, line: bytes):
        try:
            str_line = line.decode("UTF-8")
            if LocationService.NMEA_SENTENCE_GPGGA in str_line:
                msg = pynmea2.parse(str_line)
                if msg.latitude != 0.0 and msg.longitude != 0.0:
                    return Location(str(msg.latitude), str(msg.longitude))
        except:
            logging.warning(f"Could not parse GPS data {bytes}")
            return None

        return None

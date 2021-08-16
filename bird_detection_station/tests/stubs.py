from requests import Response

from bird_detection.audio.audio_services import AudioRecorderService, AudioStreamFormat

import numpy as np  # type: ignore

from bird_detection.audio.device_selection import DeviceSelector
from bird_detection.gps.location_service import LocationServiceInterface, Location
from bird_detection.http.rest_client import RestClientInterface
from bird_detection.mqtt.mqtt_service import MQTTServiceInterface
from bird_detection.weather.weather_service import WeatherServiceInterface


class DeviceSelectorMock:
    def __init__(self):
        self.selected_device = None

    @staticmethod
    def list_devices():
        return {}

    def is_device_selected(self):
        return True

    def choose_device(self):
        pass

    def select_device(self):
        pass

    def set_device(self, device_name):
        pass


class SoundDeviceStub(AudioRecorderService):
    def __init__(
        self,
        sound_device_selector: DeviceSelector = None,
        audio_format: AudioStreamFormat = None,
        threshold: float = 0.02,
    ):
        self.sample_rate = 48000
        self.channels = 1
        self.default_device: dict = {}

    def __del__(*args, **kwargs):
        pass

    def record_audio(self, record_seconds: int, wave_output_filename: str):
        pass

    def record_audio_to_numpy(
        self, record_seconds: int, blocking: bool = True
    ) -> np.ndarray:
        pass

    def is_silent(self, data, threshold: float = 0.02) -> bool:
        """
        Calculates the root mean square to indicate if a sound/noise was recorded.
        If the rms is greater than the threshold a sound occurred
        :param data:
        :param threshold:
        :return: true if the surrounding is silent and no sound was recorded
        """
        pass

    def record_sound(
        self,
        record_seconds: int = 3,
        blocking: bool = True,
        sound_directory: str = "data",
    ) -> str:
        return "Soundscape_1.wav"

    def start_audio_stream(self):
        pass

    def read_audio_stream(self):
        pass

    def close_audio_stream(self):
        pass

    def play(self, data):
        pass


class MQTTStub(MQTTServiceInterface):
    def __init__(self, mqtt_broker: str, mqtt_server_port: int):
        pass

    def publish(self, topic, payload):
        pass


class RestClientStub(RestClientInterface):
    def __init__(self, classifier_url: str):
        pass

    def post_wav(self, file_name: str):
        response = Response()
        response.status_code = 200
        response._content = b'{"Result":[{"Common Name":"Common Chaffinch","Confidence":0.6541699290275574}]}'
        return response.json()


class GPSServiceStub(LocationServiceInterface):
    def __init__(self):
        pass

    def is_GPS_sensor_attached(self) -> bool:
        return True

    def get_valid_location(self):
        return Location(lat="53.565664", lon="10.007741")


class WeatherServiceStub(WeatherServiceInterface):
    def __init__(self, lat: float = None, lon: float = None, api_key: str = None):
        pass

    def request_weather_info(self):
        weather_info = {}
        weather_info["weather"] = {"main": {}, "description": {}}
        weather_info["main"] = {}
        weather_info["wind"] = {}
        return weather_info

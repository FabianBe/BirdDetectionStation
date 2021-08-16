from bird_detection.bird_recorder_service import BirdRecorder
from bird_detection.station_type import BirdRecorderType
from tests.stubs import (
    SoundDeviceStub,
    MQTTStub,
    RestClientStub,
    GPSServiceStub,
    WeatherServiceStub,
)


def create_bird_recorder(station_type: BirdRecorderType):
    sound_device = SoundDeviceStub()
    host_url = "http://localhost"
    mqtt_service = MQTTStub("test_broker", 1883)
    rest_client = RestClientStub("test_server")
    gps_service = GPSServiceStub()
    weather_service = WeatherServiceStub()
    recording_time = 3
    accuracy_threshold = 0.6
    bird_recorder = BirdRecorder(
        station_type,
        sound_device,
        host_url,
        mqtt_service,
        rest_client,
        gps_service,
        weather_service,
        recording_time,
        accuracy_threshold,
        prediction_file="test_predictions.txt",
    )

    return bird_recorder


def create_offline_bird_recorder():
    return create_bird_recorder(BirdRecorderType.OFFLINE)


def create_offline_classification_bird_recorder():
    return create_bird_recorder(BirdRecorderType.OFFLINE_CLASSIFICATION)


def create_online_bird_recorder():
    return create_bird_recorder(BirdRecorderType.ONLINE)


def create_online_bird_recorder_without_weather():
    bird_recorder = create_bird_recorder(BirdRecorderType.ONLINE)
    bird_recorder.weather_service = None
    return bird_recorder

import os

import pytest  # type: ignore
import bird_detection.bird_recorder_service as bird_recorder_module
from bird_detection.bird_recorder_service import BirdRecorder
from tests.bird_recorder_factory import (
    create_offline_bird_recorder,
    create_online_bird_recorder,
    create_online_bird_recorder_without_weather,
)
from tests.stubs import (
    SoundDeviceStub,
    MQTTStub,
    RestClientStub,
    WeatherServiceStub,
    DeviceSelectorMock,
)


def test_create_bird_recorder(monkeypatch):
    monkeypatch.setattr(bird_recorder_module, "DeviceSelector", DeviceSelectorMock)
    monkeypatch.setattr(bird_recorder_module, "SoundDevice", SoundDeviceStub)
    monkeypatch.setattr(bird_recorder_module, "WeatherService", WeatherServiceStub)
    monkeypatch.setattr(bird_recorder_module, "MQTTService", MQTTStub)
    monkeypatch.setattr(bird_recorder_module, "RestClient", RestClientStub)
    bird_recorder = BirdRecorder.get_bird_recorder()
    assert bird_recorder is not None


@pytest.fixture()
def bird_recorder_offline():
    yield create_offline_bird_recorder()


@pytest.fixture()
def bird_recorder_online():
    yield create_online_bird_recorder()
    # Cleanup
    os.remove("test_predictions.txt")


@pytest.fixture()
def bird_recorder_online_without_weather():
    yield create_online_bird_recorder_without_weather()
    # Cleanup
    os.remove("test_predictions.txt")


def test_filter_results(bird_recorder_offline):
    prediction = {
        "Result": [
            {"Common Name": "Common Chaffinch", "Confidence": 0.6541699290275574}
        ]
    }
    filtered_prediction = bird_recorder_offline._filter_results(prediction)
    assert len(filtered_prediction) == len(prediction)

    prediction = {
        "Result": [
            {"Common Name": "Common Chaffinch", "Confidence": 0.2541699290275574}
        ]
    }
    filtered_prediction = bird_recorder_offline._filter_results(prediction)
    assert len(filtered_prediction) != len(prediction)
    assert len(filtered_prediction) == 0

    prediction = {"Result": []}
    filtered_prediction = bird_recorder_offline._filter_results(prediction)
    assert len(filtered_prediction) == 0

    prediction = {}
    filtered_prediction = bird_recorder_offline._filter_results(prediction)
    assert len(filtered_prediction) == len(prediction)


def test_process_prediction_online(bird_recorder_online):
    rest_client = RestClientStub("test_server")
    response = rest_client.post_wav("blub")
    recording_count = len(bird_recorder_online.recordings)
    bird_recorder_online._process_prediction(response, "dummyfile")
    assert recording_count + 1 == len(bird_recorder_online.recordings)
    inserted_bird = bird_recorder_online.recordings[-1]
    assert inserted_bird["Result"][0]["Common Name"] == "Common Chaffinch"


def test_process_prediction_online_without_weather(
    bird_recorder_online_without_weather,
):
    rest_client = RestClientStub("test_server")
    response = rest_client.post_wav("blub")
    recording_count = len(bird_recorder_online_without_weather.recordings)
    bird_recorder_online_without_weather._process_prediction(response, "dummyfile")
    assert recording_count + 1 == len(bird_recorder_online_without_weather.recordings)
    inserted_bird = bird_recorder_online_without_weather.recordings[-1]
    assert inserted_bird["Result"][0]["Common Name"] == "Common Chaffinch"
    assert inserted_bird["weather_info"] == "No weather data loaded"


def test_start_recording_offline(bird_recorder_offline):
    assert not bird_recorder_offline.recording
    bird_recorder_offline.start_recording()
    assert bird_recorder_offline.recording

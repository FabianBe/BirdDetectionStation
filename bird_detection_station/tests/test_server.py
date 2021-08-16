import json
import os

import pytest  # type: ignore
import requests

from fastapi.testclient import TestClient

import bird_detection.bird_recorder_service as bird_recorder_module
from bird_detection.bird_recorder_service import BirdRecorder
from tests.bird_recorder_factory import create_online_bird_recorder

from tests.stubs import (
    DeviceSelectorMock,
    MQTTStub,
    WeatherServiceStub,
    SoundDeviceStub,
    RestClientStub,
)

client = None


def mock_sound_device(monkeypatch):
    global client
    monkeypatch.setattr(bird_recorder_module, "DeviceSelector", DeviceSelectorMock)
    monkeypatch.setattr(bird_recorder_module, "SoundDevice", SoundDeviceStub)
    monkeypatch.setattr(bird_recorder_module, "WeatherService", WeatherServiceStub)
    monkeypatch.setattr(bird_recorder_module, "MQTTService", MQTTStub)
    monkeypatch.setattr(bird_recorder_module, "RestClient", RestClientStub)

    from bird_detection.http.server import app

    client = TestClient(app)


class MockResponse:
    def __init__(self):
        self.text = (
            '{"Result": [ {"Common Name": "mock_response", "Confidence": 0.99 } ] }'
        )
        self.status_code = 200

    @staticmethod
    def json():
        return {"Result": [{"Common Name": "mock_response", "Confidence": 0.99}]}


def mock_post(*args, **kwargs):
    return MockResponse()


@pytest.fixture()
def bird_recorder():
    BirdRecorder.instance = create_online_bird_recorder()
    yield
    # Cleanup
    os.remove("test_predictions.txt")


def test_toggle_recording(monkeypatch):
    mock_sound_device(monkeypatch)
    monkeypatch.setattr(requests, "post", mock_post)

    response = client.post("/actions/toggle_recording")
    assert response.status_code == 200
    assert response.json() == {"message": "Toggle recording to True"}

    response = client.get("/properties/recording")
    assert response.status_code == 200
    assert response.json()

    response = client.post("/actions/toggle_recording")
    assert response.status_code == 200
    assert response.json() == {"message": "Toggle recording to False"}


def test_get_root(monkeypatch):
    mock_sound_device(monkeypatch)
    json_response = client.get("/")
    response = json.loads(json_response.content)
    assert json_response.status_code == 200
    assert response["@context"] == "https://www.w3.org/2019/wot/td/v1"

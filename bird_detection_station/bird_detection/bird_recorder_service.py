import _thread
import asyncio
import json
import os
import logging
from asyncio import Future
from json import JSONDecodeError
from typing import List, Optional, Union

from bird_detection.audio.audio_services import AudioRecorderService
from bird_detection.audio.device_selection import (
    DeviceSelector,
)
from bird_detection.audio.sound_device_wrapper import SoundDevice
from bird_detection.config import Config
from bird_detection.gps.location_service import (
    LocationService,
    Location,
    LocationServiceInterface,
)
from bird_detection.http.rest_client import RestClient, RestClientInterface
from bird_detection.mqtt.mqtt_service import MQTTService, MQTTServiceInterface
from bird_detection.station_type import BirdRecorderType
from bird_detection.weather.weather_service import (
    WeatherService,
    WeatherServiceInterface,
)


class BirdRecorder:
    instance = None

    @staticmethod
    def get_bird_recorder():
        if not BirdRecorder.instance:
            BirdRecorder.instance = BirdRecorder.create_bird_recoder()
        return BirdRecorder.instance

    @staticmethod
    def create_bird_recoder():
        """
        A factory method for creating a BirdRecorder
        :return A BirdRecorder instance:
        """

        config = Config.get_config()

        print(
            "Please make sure that the values in the config file are correct \n"
            + str(config)
        )

        sound_device_selector = DeviceSelector()
        sound_device_selector.choose_device()

        is_silent_threshold = config.is_silent_threshold
        recording_time = config.recording_time
        accuracy_threshold = config.accuracy_threshold
        station_type = config.station_type
        host_url = config.host_url
        rest_client = None
        mqtt_service = None
        weather_service = None

        coordinates = config.gps_coordinates
        location_service = LocationService(
            Location(lat=coordinates["lat"], lon=coordinates["lon"])
        )

        if config.classifier_url:
            rest_client = RestClient(config.classifier_url)

        if config.api_key:
            location = location_service.get_valid_location()
            weather_service = WeatherService(
                float(location.lat), float(location.lon), config.api_key
            )

        if config.station_type == BirdRecorderType.ONLINE:
            mqtt_service = MQTTService(config.mqtt_broker, config.mqtt_port)

        sound_device = SoundDevice(sound_device_selector, threshold=is_silent_threshold)

        bird_recorder = BirdRecorder(
            station_type,
            sound_device,
            host_url,
            mqtt_service,
            rest_client,
            location_service,
            weather_service,
            recording_time,
            accuracy_threshold,
            config.root_dir + "/predictions.txt",
        )

        return bird_recorder

    def __init__(
        self,
        station_type: BirdRecorderType,
        audio_recorder: AudioRecorderService,
        host_url: str,
        mqtt_service: Optional[MQTTServiceInterface],
        rest_client: Optional[RestClientInterface],
        location_service: LocationServiceInterface,
        weather_service: Optional[WeatherServiceInterface],
        duration: int = 3,
        accuracy_threshold: float = 0.5,
        prediction_file: str = "predictions.txt",
    ):
        self.location_service = location_service
        self.rest_client = rest_client
        self.weather_service = weather_service
        self.mqtt_service = mqtt_service
        self.audio_recorder = audio_recorder

        self.station_type = station_type
        self.host_url = host_url
        self.recording = False
        self.recordings: List[dict] = []
        self.duration = duration
        self.accuracy_threshold = accuracy_threshold
        self.futures: List[Future] = []

        self.prediction_file = prediction_file
        if os.path.isfile(self.prediction_file):
            self._read_predictions()

    def start_recording(self):
        """
        Start the recording process in a new thread
        """
        self.recording = True
        _thread.start_new_thread(self._start_recording, ("Thread-1",))

    def stop_recording(self):
        """
        Stop the recording thread. This action is not executed immediately
        because an ongoing recording first has to be complete before the thread can finally stop
        """
        self.recording = False

    def bird_event(self):
        """
        Subscribe to the bird recorder to be informed when a bird is detected
        :return: a future of a bird event
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures.append(future)

        return future

    def _read_predictions(self):
        with open(self.prediction_file, "r+") as predictions:
            for prediction in predictions.readlines():
                prediction_dict = None
                try:
                    prediction_dict = json.loads(prediction)
                except JSONDecodeError:
                    logging.warning("Could not parse prediction file")

                if prediction_dict is not None:
                    self.recordings.append(prediction_dict)

    def _write_to_file(self, prediction: str):
        with open(self.prediction_file, "a+") as predictions:
            predictions.write(prediction + "\n")

    def _filter_results(self, prediction: dict) -> dict:
        filtered_prediction = {}
        if prediction and "Result" in prediction:
            filtered_prediction["Result"] = list(
                filter(
                    lambda result: result["Confidence"] > self.accuracy_threshold,
                    prediction["Result"],
                )
            )
            filtered_prediction = (
                filtered_prediction if filtered_prediction["Result"] else {}
            )
        return filtered_prediction

    def _start_recording(self, threadName: str):
        while self.recording:
            file_name = self.audio_recorder.record_sound(self.duration)
            if (
                self.station_type == BirdRecorderType.ONLINE
                or self.station_type == BirdRecorderType.OFFLINE_CLASSIFICATION
            ) and self.rest_client:
                prediction = self.rest_client.post_wav(file_name)
                self._process_prediction(prediction, file_name)

    def _process_prediction(self, prediction: dict, file_name: str):
        filtered_prediction = self._filter_results(prediction)
        if filtered_prediction:
            logging.info(f"New prediction {filtered_prediction}")
            location = self.location_service.get_valid_location()
            weather_info = self._get_weather_info()
            complete_prediction = self._create_complete_prediction(
                file_name, location, filtered_prediction, weather_info
            )
            self.recordings.append(complete_prediction)
            prediction_json = json.dumps(complete_prediction)
            self._write_to_file(prediction_json)
            self._publish_bird_event(prediction_json)
        else:
            os.remove("data/" + file_name)

    def _get_weather_info(self):
        if self.weather_service:
            return self.weather_service.request_weather_info()
        else:
            return "No weather data loaded"

    def _create_complete_prediction(
        self,
        file_name: str,
        location: Location,
        prediction: dict,
        weather_info: Union[dict, str],
    ) -> dict:
        return {
            "Result": prediction["Result"],
            "File": f"http://{self.host_url}/actions/files/{file_name}",
            "Time": file_name[:-4],
            "GPS": vars(location),
            "weather_info": weather_info,
        }

    def _publish_bird_event(self, json_response: str):
        if self.station_type == BirdRecorderType.ONLINE and self.mqtt_service:
            self.mqtt_service.publish("BirdEvent", json_response)
        for f in self.futures:
            if f and not f.done():
                f.set_result(json_response)
            self.futures.remove(f)

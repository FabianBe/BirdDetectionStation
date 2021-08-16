import yaml
import os
import logging

from bird_detection.station_type import BirdRecorderType


class Config:
    instance = None

    @staticmethod
    def get_config():
        if not Config.instance:
            Config.instance = Config()
        return Config.instance

    def __init__(self):
        try:
            self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config = yaml.safe_load(open("config.yml"))
            self.sound_device_name = self.config["sound_device"]
            self.host_url = self.config.get("host_url", "localhost:8000")
            self.gps_coordinates = self.config["gps_coordinates"]
            self.classifier_url = self.config["classifier_url"]
            self.is_silent_threshold = float(
                self.config.get("is_silent_threshold", 0.02)
            )
            self.recording_time = int(self.config.get("recording_time", 3))
            self.accuracy_threshold = float(self.config.get("accuracy_threshold", 0.5))
            self.station_type = BirdRecorderType[
                self.config.get("station_type", "OFFLINE").upper()
            ]
            self.api_key = self.config.get("api_key", "")
            self.mqtt_broker = str(self.config.get("mqtt_broker", "localhost"))
            self.mqtt_port = int(self.config.get("mqtt_port", 1883))
        except FileNotFoundError:
            logging.error("Config file not found. Please provide a config file")
            exit(-1)

    def __str__(self):
        return str(self.config)

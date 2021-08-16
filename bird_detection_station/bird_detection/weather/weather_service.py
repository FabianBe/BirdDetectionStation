import time
from abc import ABC, abstractmethod

import requests


class WeatherServiceInterface(ABC):
    @abstractmethod
    def request_weather_info(self) -> dict:
        pass


class WeatherService(WeatherServiceInterface):
    def __init__(self, lat: float, lon: float, api_key: str):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.units = "metric"
        self.weather_info: dict = {}
        self.last_request_time: float = 0
        self.base_url = f"http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&units={self.units}&appid={self.api_key}"

    def request_weather_info(self) -> dict:
        if time.time() > self.last_request_time + 60:
            self.base_url = f"http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&units={self.units}&appid={self.api_key}"
            req = requests.post(self.base_url)
            self.last_request_time = time.time()

            if req.status_code == 200:
                self.weather_info = {}
                json_response = req.json()
                self.weather_info["weather"] = {
                    "main": json_response["weather"][0]["main"],
                    "description": json_response["weather"][0]["description"],
                }
                self.weather_info["main"] = json_response["main"]
                self.weather_info["wind"] = json_response["wind"]

        return self.weather_info

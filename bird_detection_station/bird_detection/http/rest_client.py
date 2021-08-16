from abc import ABC, abstractmethod
from typing import Any

import requests


class RestClientInterface(ABC):
    @abstractmethod
    def post_wav(self, file_name: str) -> Any:
        pass


class RestClient(RestClientInterface):
    def __init__(self, classifier_url: str):
        self.classifier_url = classifier_url

    def post_wav(self, file_name: str):
        """
        Execute a long polling request to the classification service
        :param file_name: The filename of the recording which should be sent to the classification service
        :return: The result of the classification service
        """
        files = {"wave": (file_name, open("data/" + file_name, "rb"), "audio/x-wav")}
        post_url = self.classifier_url + "/actions/analyse"
        req = requests.post(post_url, files=files)
        prediction = None
        if req.status_code == 200 and req.json()["Result"]:
            prediction = req.json()
        return prediction

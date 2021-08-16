import logging

import sounddevice as sd  # type: ignore

from bird_detection.config import Config


class DeviceNotFoundException(Exception):
    def __init__(self, message):
        self.message = message


class DeviceSelector:
    def __init__(self):
        self.selected_device = None

    @staticmethod
    def list_devices() -> sd.DeviceList:
        """
        List information about all available devices on the system
        :return: A list of all available sound devices
        """
        return sd.query_devices()

    def is_device_selected(self):
        """
        Helper method to determine if an audio device is selected
        :return: True if an audio device is selected otherwise False
        """
        return self.selected_device is not None

    def choose_device(self):
        """
        Tries to select the default audio device based on the config file.
        If no default audio device is provided or the audio device selection
        fails an interactive menu with all available audio devices is displayed.
        """
        config = Config.get_config()
        sound_device_name = config.sound_device_name
        if sound_device_name:
            try:
                self._set_device(sound_device_name)
            except DeviceNotFoundException:
                self._select_device()
        else:
            self._select_device()

    def _select_device(self):
        device_number = None
        while device_number is None:
            print(
                "Please select the desired sound device \n" + str(self.list_devices())
            )
            try:
                device_number = int(input("Enter device number "))
                if device_number < 0 or device_number > len(self.list_devices()) - 1:
                    device_number = None
            except ValueError:
                pass

        device = self.list_devices()[device_number]
        self._set_device(device["name"])

    def _set_device(self, device_name):
        try:
            device = sd.query_devices(device_name)
            self.selected_device = device
            logging.info(f"{self.selected_device['name']} selected")
        except ValueError as ve:
            raise DeviceNotFoundException(ve)

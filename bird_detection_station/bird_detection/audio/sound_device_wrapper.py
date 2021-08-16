import os
from datetime import datetime
from scipy.io.wavfile import write  # type: ignore
import logging
import numpy as np  # type: ignore
import sounddevice as sd  # type: ignore

from bird_detection.audio.audio_services import AudioRecorderService, AudioStreamFormat
from bird_detection.audio.device_selection import DeviceSelector


class SoundDevice(AudioRecorderService):
    def __init__(
        self,
        sound_device_selector: DeviceSelector,
        threshold: float = 0.02,
    ):

        self.threshold = threshold
        self.default_device = sound_device_selector.selected_device
        self.sample_rate = 48000
        self.channels = 1

        self.stream_data = None
        sd.default.device = self.default_device["name"]
        sd.default.samplerate = 48000
        sd.default.channels = self.channels
        logging.info(
            f"New microphone {self.default_device['name']} with {self.sample_rate} sample rate and {self.channels} channels"
        )

    def __del__(self):
        if self.stream_data:
            self.close_audio_stream()

    def record_audio(self, record_seconds: int, wave_output_filename: str):
        print("Recording ....")
        my_recording = sd.rec(
            int(record_seconds * self.sample_rate),
            self.sample_rate,
            self.channels,
            blocking=True,
        )
        print("Saving ....")
        write(wave_output_filename, self.sample_rate, my_recording)  # Save as WAV file

    def record_audio_to_numpy(
        self, record_seconds: int, blocking: bool = True
    ) -> np.ndarray:
        print("Recording ....")
        my_recording = sd.rec(int(record_seconds * self.sample_rate), blocking=blocking)
        print("Saving ....")
        return my_recording

    def is_silent(self, data) -> bool:
        """
        Calculates the root mean square to indicate if a sound/noise was recorded.
        If the rms is greater than the threshold a sound occurred
        :param threshold:
        :return: true if the surrounding is silent and no sound was recorded
        """
        return np.sqrt(np.mean(data ** 2)) < self.threshold

    # TODO add recording type
    def _save_audio(self, file_name: str, recording, sound_directory: str = "data"):
        """
        Saves an audio file with the given file and sample rate into the data folder.
        If the data folder does not exist the folder will be created
        """
        if not os.path.isdir(sound_directory):
            try:
                os.mkdir(sound_directory)
            except OSError:
                print(f"Creation of the directory {sound_directory} failed")
            else:
                print(f"Successfully created the directory {sound_directory}")

        write(
            sound_directory + "/" + file_name, self.sample_rate, recording
        )  # Save as WAV file

    def record_sound(
        self,
        record_seconds: int = 3,
        blocking: bool = True,
        sound_directory: str = "data",
    ) -> str:
        import threading

        my_recording = None
        event = threading.Event()

        # indata: ndarray, frames: int, time: CData, status: CallbackFlags
        def callback(indata, frames, time, status):
            nonlocal my_recording
            if (my_recording is not None) or (not self.is_silent(indata)):
                if my_recording is None:
                    logging.info(f"Recording for {record_seconds} seconds")
                    recording = True
                    my_recording = indata.copy()
                else:
                    my_recording = np.append(my_recording, indata.copy())
                if len(my_recording) >= (self.sample_rate * record_seconds):
                    event.set()

        with sd.InputStream(
            samplerate=self.sample_rate,
            device=self.default_device["name"],
            channels=self.channels,
            callback=callback,
        ):
            event.wait()

        file_name = str(datetime.now()) + ".wav"

        self._save_audio(file_name, my_recording, sound_directory)

        return file_name

    def start_audio_stream(self):
        assert self.stream_data is None
        self.stream_data = sd.rec(int(self.sample_rate * 3600))

    def read_audio_stream(self):
        assert self.stream_data is not None
        return self.stream_data

    def close_audio_stream(self):
        assert self.stream_data is not None
        sd.stop()
        data = self.stream_data
        self.stream_data = None
        return data

    def play(self, data):
        sd.play(data, self.sample_rate, blocking=True)

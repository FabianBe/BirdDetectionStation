from abc import ABC, abstractmethod


class AudioStreamFormat:
    def __init__(
        self,
        chunk: int = 4096,
        sample_width: int = 2,
        channels: int = 2,
        sample_rate: int = 48000,
        input_device_index=None,
        output_device_index=None,
        device_name="device_name",
    ):
        self.chunk = chunk
        self.sample_width = sample_width
        self.channels = channels
        self.rate = sample_rate
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.device_name = device_name


class AudioRecorderService(ABC):
    @abstractmethod
    def record_audio(self, record_seconds: int, wave_output_filename: str):
        """
        Starts a recording from the mounted microphone for the specified record
        time in seconds, and saves the recording.

        :param record_seconds: Duration of the recording in seconds
        :param wave_output_filename: Name of WAV file to output to
        """
        pass

    @abstractmethod
    def start_audio_stream(self):
        """
        Creates an audio stream from the mounted microphone
        """
        pass

    @abstractmethod
    def read_audio_stream(self):
        """
        :return: The recorded data
        """

    @abstractmethod
    def close_audio_stream(self):
        """
        Terminates an audio stream from the mounted microphone
        """
        pass

    @abstractmethod
    def record_sound(
        self,
        record_seconds: int = 3,
        blocking: bool = True,
        sound_directory: str = "data",
    ) -> str:
        """
        This method listens to the surrounding and records any occurring sound

        :param record_seconds: If a sound occurs, the duration specifies
        how many seconds will be recorded after the occurrence
        :param blocking: Determines if the recording should be blocking
        :param sound_directory: the directory in which the sound files are saved
        """

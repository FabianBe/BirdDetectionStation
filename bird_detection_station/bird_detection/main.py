import logging
import uvicorn  # type: ignore
import signal

from bird_detection.bird_recorder_service import BirdRecorder
from bird_detection.config import Config
from bird_detection.http import server
from bird_detection.station_type import BirdRecorderType

if __name__ == "__main__":
    logging.config.dictConfig(uvicorn.config.LOGGING_CONFIG)  # type: ignore
    logging.basicConfig(level=logging.INFO)
    BirdRecorder.get_bird_recorder()
    config = Config.get_config()
    if (
        config.station_type == BirdRecorderType.ONLINE
        or config.station_type == BirdRecorderType.OFFLINE_CLASSIFICATION
    ):
        uvicorn.run(server.app, host="0.0.0.0")
        if BirdRecorder.get_bird_recorder().recording:
            BirdRecorder.get_bird_recorder().stop_recording()
    else:
        BirdRecorder.get_bird_recorder().start_recording()
        signal.pause()

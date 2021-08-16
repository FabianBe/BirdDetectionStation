import os

from fastapi import BackgroundTasks, FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from bird_detection.bird_recorder_service import BirdRecorder
from bird_detection.config import Config
from bird_detection.thing_description import ThingDescription


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(config: Config = Depends(Config.get_config)):
    td = ThingDescription(
        "bird_detection_station_02", "BirdDetectionStation", config.host_url
    )
    return td.get_thing_description()


@app.get("/properties/recording")
async def get_recording(
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    return bird_recorder.recording


@app.get("/properties/predictions")
async def get_predictions(
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    return bird_recorder.recordings


@app.get("/properties/duration")
async def get_duration(
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    return bird_recorder.duration


@app.post("/properties/duration")
async def set_duration(
    duration: int, bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder)
):
    bird_recorder.duration = duration
    return bird_recorder.duration


@app.get("/properties/location")
async def get_location(
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    location_service = bird_recorder.location_service
    location = location_service.get_valid_location()
    return vars(location)


@app.get("/actions/files/{file_name}")
async def get_file(file_name: str):
    path = "data/" + file_name
    if os.path.isfile(path):
        return FileResponse(path)
    else:
        return {"message": f"The queried file {file_name} does not exist"}


@app.post("/actions/toggle_recording")
async def toggle_recording(
    background_tasks: BackgroundTasks,
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    if not bird_recorder.recording:
        bird_recorder.recording = True
        background_tasks.add_task(bird_recorder.start_recording)
    else:
        bird_recorder.recording = False
        bird_recorder.stop_recording()
    return {"message": f"Toggle recording to {bird_recorder.recording}"}


@app.get("/events/bird_detection")
async def bird_detection(
    bird_recorder: BirdRecorder = Depends(BirdRecorder.get_bird_recorder),
):
    return {"Bird": await bird_recorder.bird_event()}

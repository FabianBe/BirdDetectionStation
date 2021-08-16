class ThingDescription:
    def __init__(self, id: str, title: str, host_name: str):
        self.id = id
        self.title = title
        self.host_name = host_name

    def get_thing_description(self) -> dict:
        return {
            "@context": "https://www.w3.org/2019/wot/td/v1",
            "id": self.id,
            "title": self.title,
            "description": "An IoT-Station which can recognize bird sounds",
            "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
            "security": ["nosec"],
            "properties": {
                "duration": {
                    "description": "The duration of the sound snippet which is captured after a sound occurred",
                    "type": "number",
                    "op": ["readproperty", "writeproperty"],
                    "minimum": 1,
                    "maximum": 3600,
                    "forms": [{"href": f"http://{self.host_name}/properties/duration"}],
                },
                "predictions": {
                    "description": "Returns the bird sound predictions which were captured during runtime",
                    "type": "string",
                    "forms": [
                        {"href": f"http://{self.host_name}/properties/predictions"}
                    ],
                },
                "location": {
                    "description": "Returns the current GPS location of the bird station",
                    "type": "string",
                    "forms": [{"href": f"http://{self.host_name}/properties/location"}],
                },
                "recording": {
                    "description": "current status of the audio recording (on = True |off = False)",
                    "type": "boolean",
                    "forms": [
                        {"href": f"http://{self.host_name}/properties/recording"}
                    ],
                },
            },
            "actions": {
                "toggle": {
                    "forms": [
                        {"href": f"http://{self.host_name}/actions/toggle_recording"}
                    ]
                }
            },
            "events": {
                "recognized_bird": {
                    "data": {"type": "string"},
                    "forms": [
                        {
                            "href": f"http://{self.host_name}/events/bird_detection",
                            "subprotocol": "longpoll",
                        }
                    ],
                }
            },
        }

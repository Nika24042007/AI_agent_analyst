import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
SCHEDULE_API_KEY = os.getenv("SCHEDULE_API_KEY")

PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]
STATIONS_PATH = os.path.join(PROJECT_DIRECTORY, "data", "stations_index.json")
ALLOWED_TRANSPORT = {"train", "plane", "suburban"}
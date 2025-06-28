# firebase_helper.py
import pyrebase
import json
import os
from dotenv import load_dotenv

load_dotenv()

def init_firebase():
    firebase_config_path = os.getenv("FIREBASE_CONFIG") or "firebase_config.json"

    with open(firebase_config_path) as f:
        config = json.load(f)

    firebase = pyrebase.initialize_app(config)
    return firebase


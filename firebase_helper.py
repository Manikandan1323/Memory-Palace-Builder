# firebase_helper.py
import pyrebase
import json
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def init_firebase():
    config = st.secrets["firebase"])
    return pyrebase.initialize_app(config)

    firebase = pyrebase.initialize_app(config)
    return firebase


# firebase_helper.py
import pyrebase
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def init_firebase():
    config = st.secrets["firebase"]
    firebase = pyrebase.initialize_app(config)
    return firebase



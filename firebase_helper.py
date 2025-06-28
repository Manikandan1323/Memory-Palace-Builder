# firebase_helper.py
import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    if not firebase_admin._apps:
        service_account_info = dict(st.secrets["firebase_admin"])
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def init_pyrebase():
    config = st.secrets["firebase"]
    return pyrebase.initialize_app(config)

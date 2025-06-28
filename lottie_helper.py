# lottie_helper.py
import requests
import streamlit as st

@st.cache_data(show_spinner=False)
def load_lottie_url(url: str):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception as e:
        print("Lottie load failed:", e)
        return None


# --- Define all animations in one place ---
LOTTIE_ANIMATIONS = {
    "brain": "https://assets10.lottiefiles.com/packages/lf20_2scSKA.json",
    "success_check": "https://assets2.lottiefiles.com/packages/lf20_jbrw3hcz.json",
    "book_open": "https://assets4.lottiefiles.com/packages/lf20_tutvdkg0.json",
    "lightbulb_idea": "https://assets1.lottiefiles.com/packages/lf20_h4th9ofg.json",
    "loading": "https://assets7.lottiefiles.com/packages/lf20_usmfx6bp.json",
    "login": "https://assets2.lottiefiles.com/packages/lf20_bdlrkrqv.json",
    "signup": "https://assets6.lottiefiles.com/private_files/lf30_ek2n2u6o.json",
    "profile_edit": "https://assets7.lottiefiles.com/packages/lf20_W6g8Zw.json",
    "scroll_up": "https://assets1.lottiefiles.com/packages/lf20_n7urc5xk.json"
}

# --- Main getter function ---
def get_lottie_animation(name: str):
    url = LOTTIE_ANIMATIONS.get(name)
    if not url:
        st.warning(f"⚠️ No animation found for '{name}'")
        return None
    return load_lottie_url(url)

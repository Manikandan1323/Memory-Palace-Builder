import streamlit as st
import re
from firebase_helper import init_firebase
from gemini import init_gemini, generate_palace_scene
import firebase_admin
from firebase_admin import credentials, firestore
import tempfile
from deep_translator import GoogleTranslator
from datetime import datetime

# --- Utility ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def translate_text(text, target_lang='hi'):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        return f"❌ Translation failed: {e}"

# --- Firebase Init ---
firebase = init_firebase()
auth = firebase.auth()
init_gemini("AIzaSyDhKieRP7DWHdXgfA-4ip8pUHBaEsiYe-c")

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- UI ---
st.set_page_config(page_title="Memory Palace Builder", layout="centered")
st.markdown("""
    <style>
    /* Base font & spacing */
    html, body {
        font-size: 16px;
        line-height: 1.6;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Streamlit containers */
    .block-container {
        padding: 1rem 1rem 3rem;
        max-width: 100% !important;
    }

    /* Mobile responsive */
    @media only screen and (max-width: 600px) {
        .block-container {
            padding: 0.5rem;
        }

        h1, h2, h3 {
            font-size: 1.2em !important;
        }

        .stButton>button {
            font-size: 0.9em;
            padding: 0.4em 1em;
        }

        .stTextInput>div>div>input,
        .stSelectbox>div>div>div {
            font-size: 1em !important;
        }

        img {
            max-width: 100% !important;
            height: auto !important;
        }
    }

    /* Back to top link spacing */
    a[href="#top"] {
        display: block;
        margin-top: 1rem;
        text-align: right;
        font-size: 0.9rem;
        color: #888;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("\U0001F9E0 Memory Palace Builder")



# --- Sidebar ---
if "user" not in st.session_state:
    st.sidebar.markdown("## Menu")
    menu = st.sidebar.radio("", ["Login", "Sign Up"], key="main_menu")
else:
    user = st.session_state["user"]
    user_id = user["localId"]
    display_name = user.get("name") or user.get("username") or user.get("email", "").split("@")[0]
    
    st.sidebar.markdown("## Mine")
    st.sidebar.image(user.get("avatar"), width=36)
    st.sidebar.markdown(f"\U0001F44B Hello, **{display_name}**")

    # 🌐 Language Preference (store both name and code)
    language_map = {
        "English": "en", "Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Kannada": "kn",
        "Bengali": "bn", "Marathi": "mr", "Gujarati": "gu", "Malayalam": "ml", "Punjabi": "pa"
    }
    selected_lang = st.sidebar.selectbox("🌍 Preferred Language", list(language_map.keys()), key="language_select")
    st.session_state["user_language"] = selected_lang
    st.session_state["lang_code"] = language_map[selected_lang]

    menu = st.sidebar.radio("", ["Generate", "My Palaces", "Profile"], key="mine_menu")
    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.experimental_rerun()


# --- Profile View/Edit ---
def show_user_profile():
    st.subheader("\U0001F464 My Profile")
    user_info = st.session_state.get("user", {})
    user_id = user_info.get("localId")
    user_doc = db.collection("users").document(user_id).get()
    data = user_doc.to_dict() if user_doc.exists else {}

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if not st.session_state.edit_mode:
        st.image(data.get("avatar", ""), width=100, caption="Avatar")
        st.markdown(f"**Name:** {data.get('name', '')}")
        st.markdown(f"**Username:** @{data.get('username', '')}")
        st.markdown(f"**Email:** {user_info.get('email', '')}")
        st.markdown(f"**Profession:** {data.get('profession', '')}")
        st.markdown(f"**About Me:**\n\n{data.get('bio', '')}")
        if st.button("✏️ Edit Profile"):
            st.session_state.edit_mode = True
    else:
        name = st.text_input("Name", data.get("name", ""))
        username = st.text_input("Username", data.get("username", ""))
        profession = st.selectbox("Profession", ["Student", "Professional", "Other"],
                                  index=["Student", "Professional", "Other"].index(data.get("profession", "Student")))
        bio = st.text_area("About Me", data.get("bio", ""))

        avatar_options = {
            "🦁 Lion": "https://api.dicebear.com/7.x/adventurer/svg?seed=Lion",
            "🐯 Tiger": "https://api.dicebear.com/7.x/adventurer/svg?seed=Tiger",
            "🐵 Monkey": "https://api.dicebear.com/7.x/adventurer/svg?seed=Monkey",
            "🐉 Dragon": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dragon",
            "🔥 Phoenix": "https://api.dicebear.com/7.x/adventurer/svg?seed=Phoenix",
            "🐺 Wolf": "https://api.dicebear.com/7.x/adventurer/svg?seed=Wolf",
            "🐻 Bear": "https://api.dicebear.com/7.x/adventurer/svg?seed=Bear",
            "🐱 Cat": "https://api.dicebear.com/7.x/adventurer/svg?seed=Cat",
            "🐶 Dog": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dog",
            "🦊 Fox": "https://api.dicebear.com/7.x/adventurer/svg?seed=Fox"
        }
        avatar_name = st.selectbox("Choose Your Avatar", list(avatar_options.keys()))
        avatar_url = avatar_options[avatar_name]
        st.image(avatar_url, width=100, caption="Selected Avatar")

        if st.button("💾 Save Profile"):
            updated = {"name": name, "username": username, "profession": profession, "bio": bio, "avatar": avatar_url}
            db.collection("users").document(user_id).set(updated, merge=True)
            st.session_state.user.update(updated)
            st.success("✅ Profile updated!")
            st.session_state.edit_mode = False
            st.experimental_rerun()

# --- Pages ---
if menu == "Login":
    st.subheader("🔐 Login")
    email = st.text_input("Email").strip()
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format")
        else:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                user_id = user["localId"]
                user_doc = db.collection("users").document(user_id).get()
                user.update(user_doc.to_dict() if user_doc.exists else {})
                st.session_state["user"] = user
                st.success("✅ Logged in successfully.")
                st.experimental_rerun()
            except Exception:
                st.error("❌ Login failed")

elif menu == "Sign Up":
    st.subheader("📝 Create Account")
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    profession = st.selectbox("Profession", ["Student", "Professional", "Other"])

    avatar_options = {
        "🦁 Lion": "https://api.dicebear.com/7.x/adventurer/svg?seed=Lion",
        "🐯 Tiger": "https://api.dicebear.com/7.x/adventurer/svg?seed=Tiger",
        "🐵 Monkey": "https://api.dicebear.com/7.x/adventurer/svg?seed=Monkey",
        "🐉 Dragon": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dragon",
        "🔥 Phoenix": "https://api.dicebear.com/7.x/adventurer/svg?seed=Phoenix",
        "🐺 Wolf": "https://api.dicebear.com/7.x/adventurer/svg?seed=Wolf",
        "🐻 Bear": "https://api.dicebear.com/7.x/adventurer/svg?seed=Bear",
        "🐱 Cat": "https://api.dicebear.com/7.x/adventurer/svg?seed=Cat",
        "🐶 Dog": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dog",
        "🦊 Fox": "https://api.dicebear.com/7.x/adventurer/svg?seed=Fox"
    }
    avatar_name = st.selectbox("Choose Your Avatar", list(avatar_options.keys()))
    avatar_url = avatar_options[avatar_name]
    st.image(avatar_url, width=100, caption="Selected Avatar")

    if st.button("Sign Up"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format")
        elif not username or not name:
            st.error("❌ Name and Username are required")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                user_id = user["localId"]
                db.collection("users").document(user_id).set({
                    "email": email, "username": username, "name": name,
                    "profession": profession, "avatar": avatar_url, "bio": ""
                })
                user.update({"username": username, "name": name, "avatar": avatar_url, "profession": profession, "bio": ""})
                st.session_state["user"] = user
                st.success("✅ Account created.")
                st.experimental_rerun()
            except Exception:
                st.error("❌ Sign up failed")

elif menu == "Generate" and "user" in st.session_state:
    st.subheader("🔮 Generate Memory Palace")
    topic = st.text_input("Enter a topic to visualize")
    locations = ["🏠 My Home", "🛕 My Temple", "🚗 My Car", "🏫 My School", "🏞️ Park", "🧘 Meditation Hall", "🏰 Imaginary Castle", "✍️ Other (let me type)"]
    choice = st.selectbox("Where should this memory go?", locations)
    location = st.text_input("Describe your place") if choice == "✍️ Other (let me type)" else choice

    
    if st.button("Generate Palace") and topic and location:
        try:
            scene = generate_palace_scene(f"{topic} stored in {location}")
            st.success("✅ Memory Palace Generated")
            st.write(scene)

            # Optional translation (if added)
            lang_code = st.session_state.get("lang_code", "en")
            if lang_code != "en":
                translated_scene = translate_text(scene, lang_code)
                st.markdown(f"### 🌐 Translated ({lang_code})")
                st.write(translated_scene)

            # Save to Firestore
            from datetime import datetime
            db.collection("users").document(st.session_state["user"]["localId"]).collection("palaces").add({
                "topic": topic,
                "scene": scene,
                "location": location,
                "created_at": datetime.utcnow()
            })
            st.success("📂 Palace saved to your collection!")
            st.experimental_rerun()

        except Exception as e:
            st.error("⚠️ Gemini quota exceeded. Try again tomorrow or upgrade your plan.")
            st.stop()


        # Translate scene
        from googletrans import Translator
        translator = Translator()
        user_language = st.session_state.get("user_language", "English")
        lang_code = st.session_state.get("lang_code", "en")
        translated_scene = translator.translate(scene, dest=lang_code).text

        # Show both versions
        st.success("✅ Memory Palace Generated")
        st.markdown("### 🧠 English Version")
        st.write(scene)
        st.markdown(f"### 🌐 Translated ({user_language})")
        st.write(translated_scene)

        # Save both to Firebase
        user_id = st.session_state["user"]["localId"]
        db.collection("users").document(user_id).collection("palaces").add({
            "topic": topic,
            "scene": scene,
            "location": location,
            "translated_scene": translated_scene,
            "language": lang_code
        })
        st.success("📂 Palace saved to your collection!")


elif menu == "My Palaces" and "user" in st.session_state:
    st.subheader("📚 My Memory Palaces")
    st.markdown("<a name='top'></a>", unsafe_allow_html=True)  # anchor for back to top

    user_id = st.session_state["user"]["localId"]
    palaces_ref = db.collection("users").document(user_id).collection("palaces").order_by("created_at", direction=firestore.Query.DESCENDING)
    docs = list(palaces_ref.stream())
    st.markdown(f"### 📊 You have {len(docs)} palace{'s' if len(docs) != 1 else ''}")

    if docs:
        for doc in docs:
            data = doc.to_dict()
            topic = data.get('topic', 'Untitled')
            location = data.get('location', 'Unknown')
            scene = data.get('scene', 'No scene found.')

            st.markdown(f"### 🏛️ {topic} — *{location}*")
            st.markdown(f"🧠 **Scene Description:**\n\n{scene}")
            st.markdown("[⬆️ Back to top](#top)", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("No memory palaces saved yet. Create one in the 'Generate' tab!")


elif menu == "Profile" and "user" in st.session_state:
    show_user_profile()

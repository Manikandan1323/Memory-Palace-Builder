import streamlit as st
import re
from firebase_helper import init_firebase
from gemini import init_gemini, generate_palace_scene
import firebase_admin
from firebase_admin import credentials, firestore

# --- Utility Functions ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def show_user_profile():
    st.subheader("👤 My Profile")
    user_info = st.session_state.get("user", {})

    default_name = user_info.get("email", "").split("@")[0]
    name = st.text_input("Display Name", user_info.get("name", default_name))
    bio = st.text_area("About Me", user_info.get("bio", ""))

    avatar_urls = [
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Lion",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Tiger",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Monkey",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Dragon",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Phoenix",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Wolf",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Bear",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Cat",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Dog",
        "https://api.dicebear.com/7.x/adventurer/svg?seed=Fox"
    ]

    if "selected_avatar" not in st.session_state:
        st.session_state.selected_avatar = user_info.get("avatar", avatar_urls[0])

    st.markdown("### Choose Your Avatar")
    cols = st.columns(5)
    for i, url in enumerate(avatar_urls):
        with cols[i % 5]:
            st.image(url, width=60)
            if st.button(f"Choose {i+1}", key=f"avatar_{i}"):
                st.session_state.selected_avatar = url

    avatar_url = st.session_state.selected_avatar
    st.markdown("### Selected Avatar")
    if avatar_url:
        st.image(avatar_url, width=120)

    if st.button("Save Profile"):
        st.session_state.user["name"] = name
        st.session_state.user["bio"] = bio
        st.session_state.user["avatar"] = avatar_url

        user_id = st.session_state["user"]["localId"]
        db.collection("users").document(user_id).set({
            "name": name,
            "bio": bio,
            "avatar": avatar_url
        }, merge=True)

        st.success("✅ Profile updated!")

# --- Init Firebase + Gemini ---
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
st.markdown("""
<style>
@media screen and (max-width: 768px) {
    section[data-testid="stSidebar"] { transform: translateX(-100%); transition: transform 0.3s ease-in-out; }
    .main { margin-left: 0; }
}
#topBtn {
  position: fixed; bottom: 30px; right: 20px; z-index: 9999;
  background-color: #6c63ff; color: white; padding: 10px 12px; font-size: 20px;
  border: none; border-radius: 50%; cursor: pointer; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
  transition: all 0.3s ease; text-decoration: none;
}
#topBtn:hover { background-color: #4f4bf7; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<a href="#top" id="topBtn" title="Go to top">⬆️</a>
""", unsafe_allow_html=True)

firebase = init_firebase()
auth = firebase.auth()
init_gemini("AIzaSyDhKieRP7DWHdXgfA-4ip8pUHBaEsiYe-c")

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

st.title("🧠 Memory Palace Builder")

# --- Sidebar ---
if "user" not in st.session_state:
    st.sidebar.markdown("## Menu")
    menu = st.sidebar.radio("", ["Login", "Sign Up"], key="main_menu")
else:
    st.sidebar.markdown("## Mine")
    user = st.session_state["user"]
    display_name = user.get("name") or user.get("email", "").split("@")[0]
    avatar_url = user.get("avatar")

    if avatar_url:
        st.sidebar.markdown(f"""
        <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
            <img src="{avatar_url}" width="36" style="border-radius: 50%;" />
            <span style='font-weight: 600;'>{display_name}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"👋 Hello, **{display_name}**")

    menu = st.sidebar.radio("", ["Generate", "My Palaces", "Profile"], key="mine_menu")

    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.experimental_rerun()

# --- Pages ---
if menu == "Login":
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format")
        else:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                user_id = user["localId"]
                user_doc = db.collection("users").document(user_id).get()
                user.update(user_doc.to_dict() if user_doc.exists else {"name": email.split("@")[0]})
                st.session_state["user"] = user
                st.success("✅ Logged in successfully.")
                st.experimental_rerun()
            except Exception:
                st.error("❌ Login failed")

elif menu == "Sign Up":
    st.subheader("📝 Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state["user"] = user
                st.success("✅ Account created.")
                st.experimental_rerun()
            except Exception:
                st.error("Sign up failed")

elif menu == "Generate" and "user" in st.session_state:
    st.subheader("🔮 Generate Memory Palace")
    topic = st.text_input("Enter a topic to visualize")
    locations = ["🏠 My Home", "🗮 My Temple", "🚗 My Car", "🏫 My School", "🏞️ Park", "🧘 Meditation Hall", "🏰 Imaginary Castle", "✍️ Other (let me type)"]
    choice = st.selectbox("Where should this memory go?", locations)
    location = st.text_input("Describe your place") if choice == "✍️ Other (let me type)" else choice

    if st.button("Generate Palace") and topic and location:
        scene = generate_palace_scene(f"{topic} stored in {location}")
        st.success("✅ Memory Palace Generated")
        st.write(scene)

        user_id = st.session_state["user"]["localId"]
        db.collection("users").document(user_id).collection("palaces").add({
            "topic": topic, "scene": scene, "location": location
        })
        st.success("📂 Saved to your palace collection")

elif menu == "My Palaces" and "user" in st.session_state:
    st.subheader("📚 My Memory Palaces")
    user_id = st.session_state["user"]["localId"]
    palaces = list(db.collection("users").document(user_id).collection("palaces").stream())

    st.markdown("### 📊 Your Learning Progress")
    st.markdown(f"• **Total Palaces:** {len(palaces)}")

    if palaces:
        latest_doc = max(palaces, key=lambda d: d.update_time)
        st.markdown(f"• **Last Updated:** {latest_doc.update_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No palaces found yet.")

    for doc in palaces:
        data = doc.to_dict()
        st.markdown(f"### 🏛️ {data.get('topic')} — *{data.get('location')}*")
        st.markdown("🧠 " + data.get("scene", "No scene found"))
        st.markdown("---")

elif menu == "Profile" and "user" in st.session_state:
    show_user_profile()

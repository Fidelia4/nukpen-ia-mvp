import streamlit as st
from PIL import Image
from analysis import analyze_outfit

st.set_page_config(page_title="Nukpɛń_IA", layout="wide")

# Charger le CSS
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

import base64
     
def load_logo():
    with open("assets/logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()
    
    st.markdown(
        f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )

load_logo()
st.subheader("Le miroir intelligent qui comprend votre style")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📷 Choisissez une option")

    option = st.radio(
        "Source de l'image :",
        ["Importer une image", "Prendre une photo"]
    )

    image = None

    if option == "Importer une image":
        uploaded_file = st.file_uploader(
            "Importer une photo de votre tenue",
            type=["jpg", "png", "jpeg"]
        )

        if uploaded_file:
            image = Image.open(uploaded_file)

    else:
        camera_photo = st.camera_input("Prenez une photo")

        if camera_photo:
            image = Image.open(camera_photo)

    occasion = st.selectbox(
        "Choisir l'occasion",
        ["Mariage", "Bureau", "Soirée", "Sortie", "Cérémonie traditionnelle"]
    )

    if image:
        st.image(image, caption="Votre tenue", use_column_width=True)

        if st.button("✨ Analyser ma tenue"):
            with st.spinner("Analyse en cours..."):
                result = analyze_outfit(image, occasion)
                st.session_state["result"] = result

with col2:
    if "result" in st.session_state:
        st.markdown("### 🧠 Résultat de l’analyse")
        st.markdown(
            f'<div class="result-box">{st.session_state["result"]}</div>',
            unsafe_allow_html=True
        )

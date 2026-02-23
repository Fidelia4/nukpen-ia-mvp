# import streamlit as st
# from PIL import Image
# from analysis import analyze_outfit
# from html import escape
# analyze_outfit(image, occasion, provider="groq")
# st.set_page_config(page_title="Nukpɛń_IA", layout="wide")

# # Charger le CSS
# def load_css():
#     with open("style.css") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# load_css()

# import base64
     
# def load_miroir():
#     with open("assets/miroir.jpeg", "rb") as img_file:
#         miroir_base64 = base64.b64encode(img_file.read()).decode()
    
#     st.markdown(
#         f"""
#         <div class="miroir-container">
#             <img src="data:image/jpeg;base64,{miroir_base64}" class="miroir-img">
#         </div>
#         """,
#         unsafe_allow_html=True
#     )


# load_miroir()
# st.subheader("Le miroir intelligent qui comprend votre style")

# st.markdown("---")

# col1, col2 = st.columns(2)

# with col1:
#     st.markdown("### 📷 Choisissez une option")

#     provider = st.selectbox(
#         "Fournisseur IA",
#         ["Ollama (local gratuit)", "OpenAI", "OpenRouter", "Groq"],
#         help="Ollama fonctionne en local sans clé API. OpenAI: OPENAI_API_KEY, OpenRouter: OPENROUTER_API_KEY, Groq: GROQ_API_KEY (dans .env)."
#     )

#     model = st.text_input(
#         "Modèle (optionnel)",
#         value="",
#         help="Laisse vide pour utiliser le modèle par défaut du fournisseur."
#     )

#     option = st.radio(
#         "Source de l'image :",
#         ["Importer une image", "Prendre une photo"]
#     )

#     image = None

#     if option == "Importer une image":
#         uploaded_file = st.file_uploader(
#             "Importer une photo de votre tenue",
#             type=["jpg", "png", "jpeg"]
#         )

#         if uploaded_file:
#             image = Image.open(uploaded_file)

#     else:
#         camera_photo = st.camera_input("Prenez une photo")

#         if camera_photo:
#             image = Image.open(camera_photo)

#     occasion = st.selectbox(
#         "Choisir l'occasion",
#         ["Mariage", "Bureau", "Soirée", "Sortie", "Cérémonie traditionnelle"]
#     )

#     if image:
#         st.image(image, caption="Votre tenue", width="stretch")

#         if st.button("✨ Analyser ma tenue"):
#             with st.spinner("Analyse en cours..."):
#                 result = analyze_outfit(
#                     image=image,
#                     occasion=occasion,
#                     provider="ollama" if provider.startswith("Ollama") else provider.lower(),
#                     model=model.strip() or None,
#                 )
#                 st.session_state["result"] = result

# with col2:
#     if "result" in st.session_state:
#         st.markdown("### 🧠 Résultat de l’analyse")
#         result_text = st.session_state["result"]

#         if result_text.startswith("⚠️ Réponse partielle du modèle"):
#             st.warning("État de la réponse : partielle")
#         elif result_text.startswith("⚠️"):
#             st.error("État de la réponse : erreur")
#         else:
#             st.success("État de la réponse : complète")

#         formatted_result = escape(result_text).replace("\n", "<br>")
#         st.markdown(
#             f'<div class="result-box">{formatted_result}</div>',
#             unsafe_allow_html=True
#         )


import streamlit as st
from PIL import Image
from analysis import analyze_outfit
from html import escape
import base64

st.set_page_config(page_title="Nukpɛń_IA", layout="wide")

# --------------------------
# Charger le CSS
# --------------------------
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --------------------------
# Afficher le miroir
# --------------------------
def load_miroir():
    with open("assets/miroir.jpeg", "rb") as img_file:
        miroir_base64 = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <div class="miroir-container">
            <img src="data:image/jpeg;base64,{miroir_base64}" class="miroir-img">
        </div>
        """,
        unsafe_allow_html=True
    )

load_miroir()
st.subheader("Le miroir intelligent qui comprend votre style")
st.markdown("---")

# --------------------------
# Interface principale
# --------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📷 Choisissez une option")

    provider = st.selectbox(
        "Fournisseur IA",
        ["OpenAI", "OpenRouter", "Groq", "Ollama (local gratuit)"],
        help="Pour OpenAI / OpenRouter / Groq, ajoute les clés dans les Secrets Streamlit."
    )

    model = st.text_input(
        "Modèle (optionnel)",
        value="",
        help="Laisse vide pour utiliser le modèle par défaut."
    )

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
        st.image(image, caption="Votre tenue", width="stretch")

        if st.button("✨ Analyser ma tenue"):
            with st.spinner("Analyse en cours..."):

                selected_provider = "ollama" if provider.startswith("Ollama") else provider.lower()

                # --------------------------
                # Appel principal de l'analyse
                # --------------------------
                result = analyze_outfit(
                    image=image,
                    occasion=occasion,
                    provider=selected_provider,
                    model=model.strip() or None,
                )

                # --------------------------
                # Fallback automatique si erreur
                # --------------------------
                if result.startswith("⚠️") and selected_provider == "openai":
                    result = analyze_outfit(image, occasion, provider="openrouter")
                if result.startswith("⚠️") and selected_provider in ["openai", "openrouter"]:
                    result = analyze_outfit(image, occasion, provider="groq")

                # Stocker le résultat et provider utilisé
                st.session_state["result"] = result
                st.session_state["provider_used"] = selected_provider

# --------------------------
# Affichage du résultat
# --------------------------
with col2:
    if "result" in st.session_state:
        st.markdown("### 🧠 Résultat de l’analyse")
        result_text = st.session_state["result"]
        provider_used = st.session_state.get("provider_used", "")

        # État de la réponse
        if result_text.startswith("⚠️ Réponse partielle du modèle"):
            st.warning("État de la réponse : partielle")
        elif result_text.startswith("⚠️"):
            st.error("État de la réponse : erreur")
        else:
            st.success("État de la réponse : complète")

        # Message explicatif logique selon provider
        if provider_used == "groq":
            st.info(
                "ℹ️ Analyse texte seulement : le service Groq ne supporte pas la génération ou amélioration d'image pour le plan actuel."
            )
        elif provider_used in ["openai", "openrouter"]:
            st.info(
                "ℹ️ L'analyse utilise l'image fournie mais aucune nouvelle image améliorée n'a été générée. Cela peut être dû au quota ou au plan actuel de votre abonnement."
            )
        elif provider_used == "ollama":
            st.info(
                "ℹ️ Analyse locale avec Ollama. L'image est utilisée pour l'analyse, mais aucune génération d'image améliorée n'est disponible en mode local."
            )

        # Affichage du texte
        formatted_result = escape(result_text).replace("\n", "<br>")
        st.markdown(
            f'<div class="result-box">{formatted_result}</div>',
            unsafe_allow_html=True
        )
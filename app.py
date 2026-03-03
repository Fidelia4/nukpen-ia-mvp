import streamlit as st
from PIL import Image
from analysis import analyze_outfit
from html import escape
import requests
import base64
import time

st.set_page_config(page_title="Nukpɛń_IA", layout="wide")


def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()


def _ollama_available() -> bool:
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=0.5)
        return resp.status_code == 200
    except Exception:
        return False


def _load_miroir_base64():
    try:
        with open("assets/miroir.jpeg", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None


def _status_meta(result_text: str):
    if result_text.startswith("⚠️ Réponse partielle du modèle"):
        return "partielle", "status-partial"
    if result_text.startswith("⚠️"):
        return "erreur", "status-error"
    return "complète", "status-ok"


def _render_splash(logo_base64: str | None):
    st.markdown(
        f"""
        <style>
            .splash-min-wrap {{
                position: fixed;
                inset: 0;
                width: 100vw;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 0.8rem;
                background: #0b1026;
                z-index: 9999;
                color: #ffffff;
            }}
            .splash-min-logo {{
                width: 118px;
                height: 118px;
                border-radius: 999px;
                object-fit: cover;
                border: 4px solid #fff;
                box-shadow: 0 12px 30px rgba(0,0,0,0.15);
            }}
            .splash-min-title {{
                margin: 0;
                font-size: clamp(2rem, 4vw, 3rem);
                color: #f7f1ff;
                font-weight: 800;
            }}
            .splash-min-wrap p,
            .splash-min-wrap span,
            .splash-min-wrap div,
            .splash-min-wrap h1,
            .splash-min-wrap h2,
            .splash-min-wrap h3 {{
                color: #ffffff !important;
            }}
        </style>
        <section class="splash-min-wrap">
            {f'<img src="data:image/jpeg;base64,{logo_base64}" class="splash-min-logo">' if logo_base64 else ''}
            <h1 class="splash-min-title">Nukpɛń_IA</h1>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if "splash_start_time" not in st.session_state:
        st.session_state["splash_start_time"] = time.time()

    elapsed = time.time() - st.session_state["splash_start_time"]
    remaining = max(0.0, 2.5 - elapsed)
    if remaining > 0:
        time.sleep(remaining)

    st.session_state["splash_seen"] = True
    st.rerun()


logo_b64 = _load_miroir_base64()

if "splash_seen" not in st.session_state:
    st.session_state["splash_seen"] = False

if not st.session_state["splash_seen"]:
    _render_splash(logo_b64)
    st.stop()
else:
    st.session_state.pop("splash_start_time", None)

st.markdown(
    f"""
    <section class="hero-wrap">
        <div class="hero-logo-wrap">
            {f'<img src="data:image/jpeg;base64,{logo_b64}" class="hero-logo">' if logo_b64 else ''}
        </div>
        <p class="hero-kicker">Nukpɛń_IA · Style Intelligence</p>
        <h1 class="hero-title">Votre miroir IA, prêt pour la vraie vie.</h1>
        <p class="hero-subtitle">Analyse instantanée de tenue, recommandations personnalisées, élégance moderne avec sensibilité culturelle béninoise.</p>
        <div class="hero-pills">
            <span class="pill">📸 Upload ou caméra</span>
            <span class="pill">🧠 Analyse assistée IA</span>
            <span class="pill">✨ Recommandations actionnables</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="steps-grid">
        <div class="step-card"><h4>1. Capture</h4><p>Importez une photo ou prenez-la en direct depuis votre appareil.</p></div>
        <div class="step-card"><h4>2. Contexte</h4><p>Sélectionnez l'occasion et le fournisseur IA selon votre environnement.</p></div>
        <div class="step-card"><h4>3. Décision</h4><p>Recevez une lecture structurée pour améliorer immédiatement votre look.</p></div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([1.02, 1], gap="large")

with left_col:
    st.markdown('<div class="panel-title">🎛️ Studio de style</div>', unsafe_allow_html=True)

    ollama_ok = _ollama_available()
    provider_options = ["OpenAI", "OpenRouter", "Groq"]
    if ollama_ok:
        provider_options.insert(0, "Ollama (local gratuit)")

    provider = st.selectbox(
        "Fournisseur IA",
        provider_options,
        help="OpenAI: OPENAI_API_KEY, OpenRouter: OPENROUTER_API_KEY, Groq: GROQ_API_KEY. Ollama s'affiche quand il est disponible en local.",
    )

    if not ollama_ok:
        st.caption("Ollama local non détecté ici. Utilisez un provider cloud pour cette session.")

    model = st.text_input(
        "Modèle (optionnel)",
        value="",
        help="Laissez vide pour le modèle par défaut du provider.",
    )

    source_mode = st.radio(
        "Source image",
        ["Importer une image", "Prendre une photo"],
        horizontal=True,
    )

    image = None
    if source_mode == "Importer une image":
        uploaded_file = st.file_uploader(
            "Photo de votre tenue",
            type=["jpg", "png", "jpeg"],
        )
        if uploaded_file:
            image = Image.open(uploaded_file)
    else:
        camera_photo = st.camera_input("Capture en direct")
        if camera_photo:
            image = Image.open(camera_photo)

    occasion = st.selectbox(
        "Occasion",
        ["Mariage", "Bureau", "Soirée", "Sortie", "Cérémonie traditionnelle"],
    )

    if image:
        st.image(image, caption="Aperçu de la tenue", width="stretch")

    run_analysis = st.button("✨ Lancer l’analyse complète", use_container_width=True, type="primary")
    if run_analysis and image:
        with st.spinner("Analyse en cours..."):
            result = analyze_outfit(
                image=image,
                occasion=occasion,
                provider="ollama" if provider.startswith("Ollama") else provider.lower(),
                model=model.strip() or None,
            )
            st.session_state["result"] = result

with right_col:
    st.markdown('<div class="panel-title">🧠 Résultat de l’analyse</div>', unsafe_allow_html=True)

    if "result" not in st.session_state:
        st.markdown(
            """
            <div class="result-empty">
                <h4>Prêt pour votre diagnostic style</h4>
                <p>Ajoutez une photo, sélectionnez l’occasion, puis lancez l’analyse pour obtenir un retour détaillé en 6 sections.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        result_text = st.session_state["result"]
        status_label, status_class = _status_meta(result_text)
        st.markdown(
            f'<div class="status-chip {status_class}">État de la réponse : {status_label}</div>',
            unsafe_allow_html=True,
        )

        formatted_result = escape(result_text).replace("\n", "<br>")
        st.markdown(
            f'<div class="result-box">{formatted_result}</div>',
            unsafe_allow_html=True,
        )

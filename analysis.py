import base64
import ast
import json
import re
import time
from openai import OpenAI
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from prompt import build_prompt
import os
from dotenv import load_dotenv
import io

load_dotenv()

REQUIRED_STYLE_KEYS = [
    "description",
    "points_forts",
    "ameliorations",
    "accessoires",
    "coiffure",
    "maquillage",
]


# ================= CLIENT =================
def _build_client(provider: str):
    provider = (provider or "openai").lower()

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None, "⚠️ Clé OPENROUTER_API_KEY manquante."
        return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1"), None

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None, "⚠️ Clé GROQ_API_KEY manquante."
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1"), None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "⚠️ Clé OPENAI_API_KEY manquante."
    return OpenAI(api_key=api_key), None


# ================= MODELES =================
def _default_model(provider: str) -> str:
    provider = (provider or "openai").lower()
    if provider == "openrouter":
        return "qwen/qwen2.5-vl-7b-instruct"
    if provider == "groq":
        return "llama-3.1-8b-instant"
    return "gpt-4.1-mini"


# ================= RESULT CHECK =================
def _is_incomplete_result(text: str) -> bool:
    if not text:
        return True

    cleaned = text.strip()
    if len(cleaned) < 150:
        return True

    found = set(re.findall(r"(?:^|\n)\s*([1-6])\s*[\.|\)]", cleaned.lower()))
    return len(found) < 6


# ================= MAIN =================
def analyze_outfit(image, occasion, provider="openai", model=None):
    client, err = _build_client(provider)
    if err:
        return err

    model_name = model or _default_model(provider)

    # Encode image
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    try:
        # ⭐ Adapter selon provider
        if provider.lower() == "groq":
            messages = [
                {"role": "system", "content": "Tu es un styliste professionnel."},
                {"role": "user", "content": build_prompt(occasion)},
            ]
        else:
            messages = [
                {"role": "system", "content": "Tu es un styliste professionnel."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_prompt(occasion)},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                    ],
                },
            ]

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=900,
        )

        content = response.choices[0].message.content

        if _is_incomplete_result(content):
            return "⚠️ Réponse partielle du modèle.\n" + content

        return content

    except RateLimitError:
        return "⚠️ Quota API insuffisant (429)."
    except AuthenticationError:
        return "⚠️ Clé API invalide."
    except (APIConnectionError, APITimeoutError):
        return "⚠️ Problème réseau API."
    except APIStatusError as e:
        return f"⚠️ Erreur API (status {e.status_code})."
    except Exception:
        return "⚠️ Erreur inattendue pendant l’analyse."
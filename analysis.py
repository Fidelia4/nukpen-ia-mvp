import base64
import ast
import json
import re
import time
import requests
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


def is_incomplete_result(text: str) -> bool:
    if not text:
        return True

    cleaned = text.strip()
    if len(cleaned) < 180:
        return True

    low = cleaned.lower()
    # Doit contenir les 6 sections (formats acceptés: 1. ou 1))
    found = set(re.findall(r"(?:^|\n)\s*([1-6])\s*[\.|\)]", low))
    if len(found) < 6:
        return True

    # Cas fréquent: le modèle renvoie seulement un titre de section
    if "améliorations recommandée" in low and len(cleaned.split()) < 20:
        return True

    return False


def _build_client(provider: str):
    provider = (provider or "openai").lower()

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None, "⚠️ Clé manquante. Ajoute OPENROUTER_API_KEY dans le fichier .env."

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        return client, None

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None, "⚠️ Clé manquante. Ajoute GROQ_API_KEY dans le fichier .env."

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        return client, None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "⚠️ Clé manquante. Ajoute OPENAI_API_KEY dans le fichier .env."

    client = OpenAI(api_key=api_key)
    return client, None


def _default_model(provider: str) -> str:
    provider = (provider or "openai").lower()
    if provider == "ollama":
        return "moondream"
    if provider == "openrouter":
        return "openai/gpt-4o-mini"
    if provider == "groq":
        return "llama-3.2-11b-vision-preview"
    return "gpt-4.1-mini"


def _encode_image_for_ollama(image) -> str:
    img = image.convert("RGB")
    img.thumbnail((768, 768))

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=80, optimize=True)
    return base64.b64encode(buffered.getvalue()).decode()


def _extract_json_block(text: str):
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        try:
            data = ast.literal_eval(cleaned)
            if isinstance(data, (dict, list)):
                return data
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            try:
                data = ast.literal_eval(match.group(0))
                if isinstance(data, (dict, list)):
                    return data
            except Exception:
                pass
            return None


def _looks_like_key_list(text: str) -> bool:
    if not text:
        return False
    cleaned = text.strip()
    if not (cleaned.startswith("[") and cleaned.endswith("]")):
        return False
    low = cleaned.lower()
    return (
        "description" in low
        and "points_forts" in low
        and "ameliorations" in low
    )


def _normalize_structured_output(text: str) -> str:
    data = _extract_json_block(text)
    if not isinstance(data, dict):
        return text

    keys = [
        ("description", "Description de la tenue"),
        ("points_forts", "Points forts"),
        ("ameliorations", "Améliorations recommandées"),
        ("accessoires", "Accessoires conseillés"),
        ("coiffure", "Coiffure adaptée"),
        ("maquillage", "Maquillage conseillé"),
    ]

    lines = []
    for idx, (k, label) in enumerate(keys, start=1):
        val = str(data.get(k, "")).strip()
        lines.append(f"{idx}. {label}")
        lines.append(val if val else "(information manquante)")
        lines.append("")

    return "\n".join(lines).strip()


def _extract_style_dict(text: str) -> dict:
    data = _extract_json_block(text)
    if not isinstance(data, dict):
        return {}

    out = {}
    for key in REQUIRED_STYLE_KEYS:
        val = data.get(key, "")
        if val is None:
            val = ""
        out[key] = str(val).strip()
    return out


def _missing_style_keys(style_data: dict) -> list[str]:
    def _is_placeholder(val: str) -> bool:
        v = (val or "").strip().lower()
        if not v:
            return True
        if v in {"0", "1", "2", "3", "n/a", "na", "none", "null", "-"}:
            return True
        if re.fullmatch(r"\d+", v):
            return True
        return False

    missing = []
    for key in REQUIRED_STYLE_KEYS:
        val = str(style_data.get(key, "")).strip()
        if len(val) < 30 or _is_placeholder(val):
            missing.append(key)
    return missing


def _merge_style_dict(base: dict, extra: dict) -> dict:
    merged = dict(base)
    for key in REQUIRED_STYLE_KEYS:
        base_val = str(merged.get(key, "")).strip()
        extra_val = str(extra.get(key, "")).strip()
        if extra_val and (not base_val or len(base_val) < len(extra_val)):
            merged[key] = extra_val
    return merged


def _format_style_dict(style_data: dict) -> str:
    ordered = {key: str(style_data.get(key, "")).strip() for key in REQUIRED_STYLE_KEYS}
    return _normalize_structured_output(json.dumps(ordered, ensure_ascii=False))


# ... toutes les autres fonctions comme _complete_missing_sections_with_text_only,
# _build_ollama_prompt, _analyze_with_ollama restent inchangées


def analyze_outfit(image, occasion, provider="openai", model=None):
    import io

    client, err = _build_client(provider)
    if err:
        return err

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    model_name = model or _default_model(provider)

    if provider.lower() == "ollama":
        img_base64_ollama = _encode_image_for_ollama(image)
        return _analyze_with_ollama(img_base64_ollama, occasion, model_name)

    try:
        response = None
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Tu es un styliste professionnel."},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": build_prompt(occasion)},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                            ],
                        },
                    ],
                    max_tokens=900,
                )
                break
            except APIStatusError as e:
                if e.status_code in (502, 503, 504) and attempt < 2:
                    time.sleep(1.2 * (attempt + 1))
                    continue
                raise

        content = response.choices[0].message.content
        if _is_incomplete_result(content):
            return "⚠️ Réponse partielle du modèle (non remplacée).\n" + content
        return content

    except RateLimitError:
        return "⚠️ Quota API insuffisant (erreur 429). Vérifie la facturation/crédits."
    except AuthenticationError:
        return "⚠️ Clé API invalide. Vérifie ton fichier .env."
    except (APIConnectionError, APITimeoutError):
        return "⚠️ Problème réseau vers l’API du fournisseur. Vérifie ta connexion."
    except APIStatusError as e:
        if e.status_code in (502, 503, 504):
            return "⚠️ Service temporairement indisponible. Réessaie plus tard."
        return f"⚠️ Erreur API (status {e.status_code})."
    except Exception:
        return "⚠️ Une erreur inattendue est survenue pendant l’analyse."

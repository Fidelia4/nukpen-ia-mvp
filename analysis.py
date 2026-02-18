# import base64
# from openai import OpenAI
# from prompt import build_prompt
# import os
# from dotenv import load_dotenv

# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def analyze_outfit(image, occasion):
#     import io
#     buffered = io.BytesIO()
#     image.save(buffered, format="PNG")
#     img_base64 = base64.b64encode(buffered.getvalue()).decode()

#     response = client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role":"system","content":"Tu es un styliste professionnel."},
#             {"role":"user","content":[
#                 {"type":"text","text":build_prompt(occasion)},
#                 {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_base64}"}}
#             ]}
#         ],
#         max_tokens=800
#     )

#     return response.choices[0].message.content
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

<<<<<<< HEAD
def analyze_outfit(image, occasion):

=======

def _is_incomplete_result(text: str) -> bool:
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
    import io

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
        # Trop court = potentiellement incomplet
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
    ordered = {
        key: str(style_data.get(key, "")).strip() for key in REQUIRED_STYLE_KEYS
    }
    return _normalize_structured_output(json.dumps(ordered, ensure_ascii=False))


def _complete_missing_sections_with_text_only(
    model_name: str,
    occasion: str,
    current_data: dict,
    missing: list[str],
):
    completion_prompt = (
        "Tu reçois une analyse partielle de tenue. "
        "Complète UNIQUEMENT les sections manquantes, en français, en JSON valide avec les 6 clés. "
        "Chaque clé doit contenir au moins 2 phrases complètes et utiles. "
        "Interdiction d'utiliser des placeholders comme 0,1,2. "
        f"Occasion: {occasion}. "
        f"Clés manquantes prioritaires: {', '.join(missing)}. "
        f"Analyse partielle actuelle: {json.dumps(current_data, ensure_ascii=False)}"
    )

    payload = {
        "model": model_name,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.25,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_predict": 500,
        },
        "messages": [
            {"role": "system", "content": "Tu es un styliste professionnel."},
            {"role": "user", "content": completion_prompt},
        ],
    }

    resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=240)
    if resp.status_code >= 400:
        return {}

    raw = resp.json().get("message", {}).get("content", "")
    return _extract_style_dict(raw)


def _build_ollama_prompt(occasion: str) -> str:
    return f"""
Analyse la tenue de l'image pour l'occasion: {occasion}.

Retourne UNIQUEMENT un JSON valide avec exactement ces clés:
- description
- points_forts
- ameliorations
- accessoires
- coiffure
- maquillage

Contraintes:
- 2 phrases minimum par clé.
- Conseils concrets (couleurs, coupe, texture, accessoires).
- Si un détail est incertain, écris une hypothèse + une alternative.
- Pas de markdown, pas de texte hors JSON.
""".strip()


def _analyze_with_ollama(img_base64: str, occasion: str, model_name: str):
    prompt = _build_ollama_prompt(occasion)

    try:
        payload = {
            "model": model_name,
            "format": "json",
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "num_predict": 420,
            },
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un styliste professionnel.",
                },
                {
                    "role": "user",
                    "content": prompt,
                    "images": [img_base64],
                },
            ],
        }

        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=900)

        if response.status_code == 404:
            return f"⚠️ Modèle Ollama introuvable: {model_name}. Exécute `ollama pull {model_name}` puis réessaie."

        if response.status_code >= 400:
            return f"⚠️ Erreur Ollama (status {response.status_code}). Vérifie que le modèle est installé puis réessaie."

        data = response.json()
        raw_content = data.get("message", {}).get("content", "")
        style_data = _extract_style_dict(raw_content)

        # Moondream renvoie parfois seulement une liste de clés: on bascule sur llava.
        if (not style_data or _looks_like_key_list(raw_content)) and model_name == "moondream":
            retry = _analyze_with_ollama(img_base64, occasion, "llava:7b")
            if not retry.startswith("⚠️"):
                return "ℹ️ Moondream a renvoyé une sortie partielle, bascule automatique sur llava:7b.\n\n" + retry

        content = _format_style_dict(style_data) if style_data else _normalize_structured_output(raw_content)

        if style_data and not _missing_style_keys(style_data):
            return content
        if not style_data and not _is_incomplete_result(content):
            return content

        # 1 tentative de réparation
        missing = _missing_style_keys(style_data) if style_data else REQUIRED_STYLE_KEYS
        repair_payload = {
            **payload,
            "messages": payload["messages"] + [
                {
                    "role": "assistant",
                    "content": raw_content,
                },
                {
                    "role": "user",
                    "content": (
                        "Ta réponse est incomplète. Renvoie UNIQUEMENT un JSON valide. "
                        f"Complète en priorité ces clés manquantes: {', '.join(missing)}. "
                        "Chaque clé doit contenir au moins 2 phrases."
                    ),
                },
            ],
        }

        repair_response = requests.post("http://localhost:11434/api/chat", json=repair_payload, timeout=900)
        if repair_response.status_code < 400:
            repaired_raw = repair_response.json().get("message", {}).get("content", "")
            repaired_data = _extract_style_dict(repaired_raw)
            if repaired_data:
                merged = _merge_style_dict(style_data, repaired_data)
                merged_text = _format_style_dict(merged)
                remaining = _missing_style_keys(merged)
                if not remaining:
                    return merged_text

                # Dernière passe: compléter les sections manquantes sans image
                completed_data = _complete_missing_sections_with_text_only(
                    model_name=model_name,
                    occasion=occasion,
                    current_data=merged,
                    missing=remaining,
                )
                if completed_data:
                    final_merged = _merge_style_dict(merged, completed_data)
                    final_text = _format_style_dict(final_merged)
                    if not _missing_style_keys(final_merged):
                        return final_text

                return (
                    "⚠️ Réponse partielle du modèle. Certaines sections restent incomplètes.\n\n"
                    f"{merged_text}"
                )

            repaired = _normalize_structured_output(repaired_raw)
            if not _is_incomplete_result(repaired):
                return repaired

        return (
            "⚠️ Réponse partielle du modèle. Essaie une autre image plus nette ou refais une tentative.\n\n"
            f"{content}"
        )

    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama n’est pas démarré. Lance `ollama serve` puis réessaie."
    except requests.exceptions.Timeout:
        if model_name != "moondream":
            retry = _analyze_with_ollama(img_base64, occasion, "moondream")
            if not retry.startswith("⚠️"):
                return "ℹ️ Modèle initial trop lent, bascule automatique sur moondream.\n\n" + retry
        return "⚠️ Ollama met trop de temps à répondre. Utilise le modèle moondream et réessaie."
    except Exception:
        return "⚠️ Une erreur inattendue est survenue pendant l’analyse locale Ollama."


def analyze_outfit(image, occasion, provider="openai", model=None):
    import io
>>>>>>> 156b52d38d7ada3a63245f765cf4b840823e35d6
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

<<<<<<< HEAD
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Tu es un styliste professionnel spécialisé en mode africaine et contemporaine."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt(occasion)},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=900
    )
=======
    model_name = model or _default_model(provider)
>>>>>>> 156b52d38d7ada3a63245f765cf4b840823e35d6

    if (provider or "openai").lower() == "ollama":
        img_base64_ollama = _encode_image_for_ollama(image)
        return _analyze_with_ollama(img_base64_ollama, occasion, model_name)

    client, err = _build_client(provider)
    if err:
        return err

    try:
        response = None
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role":"system","content":"Tu es un styliste professionnel."},
                        {"role":"user","content":[
                            {"type":"text","text":build_prompt(occasion)},
                            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img_base64}"}}
                        ]}
                    ],
                    max_tokens=800
                )
                break
            except APIStatusError as e:
                if e.status_code in (502, 503, 504) and attempt < 2:
                    time.sleep(1.2 * (attempt + 1))
                    continue
                raise

        content = response.choices[0].message.content
        if _is_incomplete_result(content):
            return (
                "⚠️ Réponse partielle du modèle (non remplacée). "
                "Refais une tentative ou change de modèle.\n\n"
                f"{content}"
            )
        return content

    except RateLimitError:
        return (
            "⚠️ Quota API insuffisant (erreur 429). "
            "Vérifie la facturation/crédits de ton fournisseur puis réessaie."
        )
    except AuthenticationError:
        if (provider or "openai").lower() == "openrouter":
            return "⚠️ Clé API invalide. Vérifie OPENROUTER_API_KEY dans le fichier .env."
        if (provider or "openai").lower() == "groq":
            return "⚠️ Clé API invalide. Vérifie GROQ_API_KEY dans le fichier .env."
        return "⚠️ Clé API invalide. Vérifie OPENAI_API_KEY dans le fichier .env."
    except (APIConnectionError, APITimeoutError):
        return "⚠️ Problème réseau vers l’API du fournisseur. Vérifie ta connexion puis réessaie."
    except APIStatusError as e:
        if e.status_code in (502, 503, 504):
            return "⚠️ Service temporairement indisponible (502/503/504). Réessaie dans 1 à 2 minutes ou change de fournisseur."
        return f"⚠️ Erreur API (status {e.status_code}). Réessaie dans quelques instants."
    except Exception:
        return "⚠️ Une erreur inattendue est survenue pendant l’analyse."

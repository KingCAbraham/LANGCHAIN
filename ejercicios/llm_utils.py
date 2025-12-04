# ejercicios/llm_utils.py
import os
from typing import List, Dict, Any

import google.generativeai as genai
from groq import Groq

# google-api-core se usa para detectar errores de cuota de forma más fina
try:
    from google.api_core import exceptions as gexc  # type: ignore
except Exception:  # por si en alguna instalación no viene
    gexc = None  # type: ignore

# ==============================
# CONFIGURACIÓN GEMINI
# ==============================

_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GOOGLE_AI_API_KEY")
    or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
)

if not _API_KEY:
    raise RuntimeError(
        "No se encontró API key para Gemini.\n"
        "Configura alguna de estas variables de entorno:\n"
        "  - GEMINI_API_KEY\n"
        "  - GOOGLE_API_KEY\n"
        "  - GOOGLE_AI_API_KEY\n"
        "  - GOOGLE_GENERATIVE_AI_API_KEY\n"
    )

genai.configure(api_key=_API_KEY)

# Modelo de lenguaje por defecto (Gemini)
_DEFAULT_LLM_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Modelo de embeddings por defecto (Gemini)
_DEFAULT_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# ==============================
# CONFIGURACIÓN GROQ (FALLBACK)
# ==============================

_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")


def _call_llm_groq(prompt: str, system: str | None = None) -> str:
    """
    Llama a Groq como fallback cuando Gemini falla (por cuota, etc.).
    """
    if not _GROQ_API_KEY:
        raise RuntimeError(
            ""
        )

    client = Groq(api_key=_GROQ_API_KEY)

    mensajes = []
    if system:
        mensajes.append({"role": "system", "content": system})
    mensajes.append({"role": "user", "content": prompt})

    try:
        chat = client.chat.completions.create(
            model=_GROQ_MODEL_NAME,
            messages=mensajes,
        )
    except Exception as e:
        raise RuntimeError(f"Error al llamar al modelo de Groq '{_GROQ_MODEL_NAME}': {e}")

    contenido = chat.choices[0].message.content
    return f"\n{contenido.strip()}"


# ==============================
# FUNCIONES PÚBLICAS
# ==============================

def call_llm(
    prompt: str,
    system: str | None = None,
    model_name: str | None = None,
) -> str:
    """
    Llama a un modelo de lenguaje de Gemini.
    Si hay error de cuota (429 / ResourceExhausted), intenta Groq como fallback.
    """
    model_id = model_name or _DEFAULT_LLM_MODEL

    parts = []
    if system:
        parts.append(system)
    parts.append(prompt)

    try:
        model = genai.GenerativeModel(model_id)
        response = model.generate_content(parts)
    except Exception as e:
        # ¿Es error de cuota / rate-limit?
        msg = str(e)
        is_quota = (
            "429" in msg
            or "rate limit" in msg.lower()
            or "quota" in msg.lower()
            or (gexc is not None and isinstance(e, gexc.ResourceExhausted))
        )
        if is_quota:
            # Intentamos fallback con Groq
            return _call_llm_groq(prompt, system)

        # Si es otro tipo de error, lo re-lanzamos
        raise RuntimeError(f"Error al llamar al modelo '{model_id}': {e}")

    # Si Gemini respondió bien:
    text = getattr(response, "text", None)
    if not text and hasattr(response, "candidates"):
        for cand in response.candidates:
            if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                piezas = []
                for p in cand.content.parts:
                    if hasattr(p, "text") and p.text:
                        piezas.append(p.text)
                if piezas:
                    text = "".join(piezas)
                    break

    return (text or "").strip()


def embed_text(
    text: str,
    model_name: str | None = None,
) -> List[float]:
    """
    Obtiene el embedding de un texto usando la API de embeddings de Gemini.
    (Aquí no hago fallback porque Groq no tiene embeddings compatibles
    de forma directa; si te quedas sin cuota de embeddings, el ej. 8
    marcará error y la interfaz lo mostrará.)
    """
    model_id = model_name or _DEFAULT_EMBED_MODEL
    text = (text or "").replace("\n", " ")

    try:
        res: Dict[str, Any] = genai.embed_content(
            model=model_id,
            content=text,
        )  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Error al llamar al modelo de embeddings '{model_id}': {e}")

    if isinstance(res, dict):
        emb = res.get("embedding", [])
    else:
        emb = getattr(res, "embedding", None)

    return list(emb or [])

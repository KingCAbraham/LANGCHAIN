# gemini_client.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Fallback opcional: Groq (Llama 3)
try:
    from groq import Groq
except Exception:
    Groq = None

load_dotenv()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("LC_MODEL", "gemini-2.5-flash")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def _is_quota_error(e: Exception) -> bool:
    s = str(e).lower()
    return "429" in s or "quota" in s or "rate limit" in s or "resourceexhausted" in s

# ------------ Fallback Groq ------------
class _GroqOneShot:
    def __init__(self):
        self.enabled = Groq is not None and bool(os.getenv("GROQ_API_KEY"))
        if self.enabled:
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def ask(self, prompt: str) -> str | None:
        if not self.enabled:
            return None
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return r.choices[0].message.content

_groq = _GroqOneShot()

# ------------ Gemini (con fallback) ------------
class GeminiOneShot:
    """Modo sin memoria: pregunta-respuesta. Fallback automático si hay 429/quota."""
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        if not GEMINI_KEY:
            # sin clave gemini -> intentar directo Groq
            self.model = None
        else:
            self.model = genai.GenerativeModel(self.model_name)

    def ask(self, prompt: str) -> str:
        if self.model is None:
            alt = _groq.ask(prompt)
            if alt:
                return alt
            raise RuntimeError("No hay clave de Gemini y no se configuró GROQ_API_KEY.")
        try:
            resp = self.model.generate_content(prompt)
            return getattr(resp, "text", str(resp))
        except Exception as e:
            if _is_quota_error(e):
                alt = _groq.ask(prompt)
                if alt:
                    return f"(fallback Groq)\n{alt}"
            raise

class GeminiChatSession:
    """Chat con 'memoria'. Fallback a Groq si Gemini tira 429."""
    def __init__(self, model_name: str = DEFAULT_MODEL, limit_turns: int | None = None):
        self.model_name = model_name
        self.limit_turns = limit_turns
        self.turns = 0
        self._new_chat()

    def _new_chat(self):
        if GEMINI_KEY:
            self.model = genai.GenerativeModel(self.model_name)
            self.chat = self.model.start_chat(history=[])
        else:
            self.model = None
            self.chat = None
        self.turns = 0

    def send(self, prompt: str) -> str:
        if self.limit_turns is not None and self.turns >= self.limit_turns:
            self._new_chat()
        if self.chat is None:
            alt = _groq.ask(prompt)
            if alt:
                return alt
            raise RuntimeError("No hay clave de Gemini y no se configuró GROQ_API_KEY.")
        try:
            resp = self.chat.send_message(prompt)
            self.turns += 1
            return getattr(resp, "text", str(resp))
        except Exception as e:
            if _is_quota_error(e):
                alt = _groq.ask(prompt)
                if alt:
                    return f"\n{alt}"
            raise

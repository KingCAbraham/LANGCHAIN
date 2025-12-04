# ejercicios/ej8_rag.py
import math
import re
from pathlib import Path
from typing import List, Tuple

try:
    from pypdf import PdfReader  # pip install pypdf
except ImportError:  # mensaje más amigable si falta
    PdfReader = None  # type: ignore

from .llm_utils import call_llm, embed_text


def _cargar_texto_pdf(pdf_path: str) -> str:
    if PdfReader is None:
        raise RuntimeError(
            "Para usar el ejercicio 8 necesitas instalar 'pypdf':\n"
            "    pip install pypdf"
        )
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el PDF: {pdf_path}")

    reader = PdfReader(str(p))
    textos: List[str] = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt:
            textos.append(txt)
    return "\n".join(textos)


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 200) -> List[str]:
    """
    Divide un texto largo en chunks solapados.
    """
    text = text.replace("\r", " ")
    words = text.split()
    chunks: List[str] = []
    start = 0
    n = len(words)

    while start < n:
        end = min(n, start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)

    return chunks


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _lexical_score(question: str, chunk: str) -> float:
    """
    Puntaje simple por coincidencia de palabras clave
    (fallback cuando los embeddings no están disponibles).
    """
    def norm(t: str) -> List[str]:
        t = t.lower()
        t = re.sub(r"[^a-záéíóúñ0-9]+", " ", t)
        return t.split()

    q_tokens = set(norm(question))
    c_tokens = set(norm(chunk))
    if not q_tokens or not c_tokens:
        return 0.0
    inter = len(q_tokens & c_tokens)
    return inter / (len(q_tokens) + 1e-6)


def run_ej8(pregunta: str, pdf_path: str) -> str:
    """
    Ejercicio 8: RAG sobre un PDF.
    - Intenta usar embeddings para buscar los fragmentos relevantes.
    - Si falla (por ejemplo, error de cuota 429), hace búsqueda por palabras clave.
    """
    pregunta = (pregunta or "").strip()
    if not pregunta:
        return "No se recibió ninguna pregunta."

    texto_pdf = _cargar_texto_pdf(pdf_path)
    if not texto_pdf.strip():
        return "No se pudo extraer texto del PDF."

    chunks = _chunk_text(texto_pdf, chunk_size=220, overlap=50)
    if not chunks:
        return "No se pudieron generar fragmentos de texto para el PDF."

    scores: List[Tuple[float, str]] = []
    uso_embeddings = True
    error_embeddings = ""

    # 1) Intentar con embeddings
    try:
        emb_q = embed_text(pregunta)
        for ch in chunks:
            emb_ch = embed_text(ch)
            score = _cosine_similarity(emb_q, emb_ch)
            scores.append((score, ch))
    except Exception as e:
        # Fallback: búsqueda lexical
        uso_embeddings = False
        error_embeddings = str(e)
        scores = []
        for ch in chunks:
            score = _lexical_score(pregunta, ch)
            scores.append((score, ch))

    # Si todos los scores son cero, al menos toma los primeros fragmentos
    scores.sort(key=lambda x: x[0], reverse=True)
    if not scores or all(s <= 0 for s, _ in scores):
        top_chunks = chunks[:3]
    else:
        top_chunks = [ch for _, ch in scores[:3]]

    contexto = "\n\n---\n\n".join(top_chunks)

    nota_fallback = ""
    if not uso_embeddings:
        nota_fallback = (
            "\n\nNOTA: No se pudieron usar embeddings (probablemente por límite de cuota). "
            "Los fragmentos se seleccionaron por coincidencia de palabras clave."
            f"\nDetalle técnico: {error_embeddings[:200]}"
        )

    prompt = f"""Eres un asistente que responde preguntas sobre un documento PDF.

Pregunta del usuario:
{pregunta}

A continuación tienes los fragmentos más relevantes del documento:

{contexto}
{nota_fallback}

Usa exclusivamente la información de estos fragmentos para responder.
Si la respuesta no está en el documento, dilo claramente.
Responde en español, de forma clara y breve.
"""
    respuesta = call_llm(prompt)
    return respuesta

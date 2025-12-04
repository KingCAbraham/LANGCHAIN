# ejercicios/ej4_parseo.py

import json
import re

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from .llm_utils import call_llm


def _llm_from_prompt_value(pv) -> str:
    if hasattr(pv, "to_string"):
        texto = pv.to_string()
    else:
        texto = str(pv)
    return call_llm(texto)


llm_runnable = RunnableLambda(_llm_from_prompt_value)

prompt = PromptTemplate.from_template(
    """Tienes este contexto:

{contexto}

Y esta instrucción:

{instruccion}

Debes contestar devolviendo SOLO un JSON válido, sin texto adicional,
con la siguiente estructura:

{{
  "respuesta": "texto con la respuesta en español",
  "puntos_clave": ["punto 1", "punto 2", "..."],
  "nivel_confianza": 0.0
}}

- "nivel_confianza" es un número entre 0 y 1.
- "puntos_clave" es una lista de frases cortas.
Devuelve únicamente el JSON, sin explicaciones.
"""
)

raw_chain = prompt | llm_runnable | StrOutputParser()


def _extraer_json(texto: str) -> str:
    """
    Intenta extraer un bloque JSON del texto.
    Si no lo encuentra, devuelve el texto completo.
    """
    match = re.search(r"\{.*\}", texto, re.S)
    if match:
        return match.group(0)
    return texto


def run_ej4(contexto: str, instruccion: str) -> str:
    ctx = (contexto or "").strip()
    inst = (instruccion or "").strip()

    if not ctx or not inst:
        return "Debes escribir algo en ambos prompts."

    bruto = raw_chain.invoke({"contexto": ctx, "instruccion": inst})
    json_str = _extraer_json(bruto)

    try:
        data = json.loads(json_str)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        # Si el JSON viene mal, devolvemos lo que respondió el modelo
        return bruto

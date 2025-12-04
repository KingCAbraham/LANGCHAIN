# ejercicios/ej3_simple_sequential.py

from operator import itemgetter

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

# Paso 1: simplificar / resumir el contexto
prompt_simplifica = PromptTemplate.from_template(
    """Reescribe el siguiente texto en un lenguaje sencillo y resumido,
como si se lo explicaras a un estudiante de secundaria.
Máximo 8 líneas.

Texto original:
{contexto}"""
)

simplify_step = prompt_simplifica | llm_runnable | StrOutputParser()

# Paso 2: responder usando el contexto simplificado
prompt_final = PromptTemplate.from_template(
    """Contexto en lenguaje sencillo:

{ctx_simple}

Instrucción del usuario:
{instruccion}

Usa exclusivamente el contexto simplificado para responder.
Si falta información, dilo explícitamente.
Responde en español.
"""
)

chain = (
    {
        "ctx_simple": simplify_step,         # usa 'contexto' internamente
        "instruccion": itemgetter("instruccion"),
    }
    | prompt_final
    | llm_runnable
    | StrOutputParser()
)


def run_simple_sequential(contexto: str, instruccion: str) -> str:
    ctx = (contexto or "").strip()
    inst = (instruccion or "").strip()

    if not ctx or not inst:
        return "Debes escribir algo en ambos prompts."

    return chain.invoke({"contexto": ctx, "instruccion": inst})

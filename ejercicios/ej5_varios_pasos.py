# ejercicios/ej5_varios_pasos.py

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

# Paso 1: generar un plan
prompt_plan = PromptTemplate.from_template(
    """Contexto:

{contexto}

Instrucción del usuario:
{instruccion}

1) Analiza brevemente qué está pidiendo el usuario.
2) Propón un plan de solución como lista numerada (1, 2, 3...).
3) NO des la respuesta final todavía.

Devuelve solo el análisis y el plan, en español.
"""
)

plan_step = prompt_plan | llm_runnable | StrOutputParser()

# Paso 2: respuesta final usando el plan
prompt_final = PromptTemplate.from_template(
    """Contexto:

{contexto}

Plan de solución:

{plan}

Instrucción del usuario:
{instruccion}

Siguiendo el plan y usando únicamente el contexto,
da una respuesta final clara en español.
Si falta información en el contexto, dilo explícitamente.
"""
)

chain = (
    {
        "contexto": itemgetter("contexto"),
        "plan": plan_step,
        "instruccion": itemgetter("instruccion"),
    }
    | prompt_final
    | llm_runnable
    | StrOutputParser()
)


def run_ej5(contexto: str, instruccion: str) -> str:
    ctx = (contexto or "").strip()
    inst = (instruccion or "").strip()

    if not ctx or not inst:
        return "Debes escribir algo en ambos prompts."

    return chain.invoke({"contexto": ctx, "instruccion": inst})

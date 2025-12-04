# ejercicios/ej1_llmchain.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from .llm_utils import call_llm


# Adaptador: PromptValue -> str -> call_llm
def _llm_from_prompt_value(pv) -> str:
    if hasattr(pv, "to_string"):
        texto = pv.to_string()
    else:
        texto = str(pv)
    return call_llm(texto)


llm_runnable = RunnableLambda(_llm_from_prompt_value)

prompt = PromptTemplate.from_template(
    """Tienes el siguiente contexto:

{contexto}

Y la siguiente instrucción del usuario:

{instruccion}

Usa únicamente la información relevante del contexto para responder.
Si el contexto no tiene la información, dilo explícitamente.
Responde de forma clara y concisa en español.
"""
)

chain = prompt | llm_runnable | StrOutputParser()


def run_llmchain(contexto: str, instruccion: str) -> str:
    ctx = (contexto or "").strip()
    inst = (instruccion or "").strip()

    if not ctx or not inst:
        return "Debes escribir algo en ambos prompts."

    return chain.invoke({"contexto": ctx, "instruccion": inst})

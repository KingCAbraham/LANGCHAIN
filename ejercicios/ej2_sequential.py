# ejercicios/ej2_sequential.py

from operator import itemgetter

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from .llm_utils import call_llm


def _llm_from_prompt_value(pv) -> str:
    """
    Convierte el PromptValue de LangChain a texto y llama a call_llm.
    """
    if hasattr(pv, "to_string"):
        texto = pv.to_string()
    else:
        texto = str(pv)
    return call_llm(texto)


llm_runnable = RunnableLambda(_llm_from_prompt_value)

# 1) Primer prompt: recibe {"input1": "..."}
prompt_uno = PromptTemplate.from_template("{input1}")
primer_paso = prompt_uno | llm_runnable | StrOutputParser()

# 2) Segundo prompt: recibe {"primer_resultado": "...", "input2": "..."}
prompt_dos = PromptTemplate.from_template(
    "Texto original:\n{primer_resultado}\n\nInstrucciones:\n{input2}"
)

# 3) Un solo chain que hace los dos pasos
chain = (
    {
        "primer_resultado": primer_paso,     # usa input1 internamente
        "input2": itemgetter("input2"),      # toma input2 del dict de entrada
    }
    | prompt_dos
    | llm_runnable
    | StrOutputParser()
)


def run_sequential(prompt_1: str, prompt_2: str) -> str:
    p1 = (prompt_1 or "").strip()
    p2 = (prompt_2 or "").strip()

    if not p1 or not p2:
        return "Debes escribir los dos prompts (Prompt 1 y Prompt 2)."

    return chain.invoke({"input1": p1, "input2": p2})

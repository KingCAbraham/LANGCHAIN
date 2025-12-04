# ejercicios/ej6_memoria.py
from typing import List, Tuple
from .llm_utils import call_llm

# Historial simple en memoria: lista de (rol, mensaje)
# rol: "user" o "assistant"
_conversacion: List[Tuple[str, str]] = []


def _historial_como_texto(max_turnos: int = 10) -> str:
    """
    Toma los últimos N turnos de la conversación y los convierte en texto.
    """
    ultimos = _conversacion[-max_turnos:]
    lineas: List[str] = []
    for rol, msg in ultimos:
        pref = "Usuario" if rol == "user" else "Asistente"
        lineas.append(f"{pref}: {msg}")
    return "\n".join(lineas)


def run_ej6(mensaje_usuario: str) -> str:
    """
    Ejercicio 6: chat con memoria en la sesión (no persistente en disco).
    """
    global _conversacion
    mensaje_usuario = (mensaje_usuario or "").strip()
    if not mensaje_usuario:
        return "No se recibió ningún mensaje."

    # Añadimos el mensaje del usuario al historial
    _conversacion.append(("user", mensaje_usuario))
    historial = _historial_como_texto()

    prompt = f"""Eres un asistente de chat con memoria de corto plazo.

Historial reciente de la conversación:
{historial}

Con base en el historial, responde al último mensaje del usuario.
Responde en español, de forma breve y natural.
"""
    respuesta = call_llm(prompt)

    # Guardamos la respuesta también en el historial
    _conversacion.append(("assistant", respuesta))

    return respuesta

# ejercicios/ej7_persistencia.py

import json
from pathlib import Path
from typing import List, Dict, Any

from .llm_utils import call_llm

# Carpeta raíz del proyecto (donde está main.py)
BASE_DIR = Path(__file__).resolve().parents[1]
MEM_FILE = BASE_DIR / "memoria_ui.json"


def _cargar_memoria() -> List[Dict[str, Any]]:
    """
    Lee la memoria persistente desde memoria_ui.json.
    Formato: lista de dicts {"role": "user"|"assistant", "content": str}
    """
    if not MEM_FILE.exists():
        return []
    try:
        with MEM_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _guardar_memoria(conversacion: List[Dict[str, Any]]) -> None:
    """
    Guarda la conversación completa en memoria_ui.json.
    """
    try:
        with MEM_FILE.open("w", encoding="utf-8") as f:
            json.dump(conversacion, f, ensure_ascii=False, indent=2)
    except Exception:
        # No tiramos la app si algo falla al escribir.
        pass


def _historial_como_texto(conv: List[Dict[str, Any]], max_mensajes: int = 20) -> str:
    """
    Convierte los últimos N mensajes a texto, similar al ejercicio 6.
    """
    ultimos = conv[-max_mensajes:]
    lineas: List[str] = []
    for msg in ultimos:
        rol = msg.get("role", "user")
        contenido = msg.get("content", "")
        pref = "Usuario" if rol == "user" else "Asistente"
        lineas.append(f"{pref}: {contenido}")
    return "\n".join(lineas)


def run_ej7(mensaje_usuario: str) -> str:
    """
    Chat con memoria persistente.
    Igual idea que el ejercicio 6, pero guardando en memoria_ui.json.
    """
    mensaje_usuario = (mensaje_usuario or "").strip()
    if not mensaje_usuario:
        return "No se recibió ningún mensaje."

    # 1) Cargar historial desde JSON y agregar el nuevo mensaje del usuario
    conv = _cargar_memoria()
    conv.append({"role": "user", "content": mensaje_usuario})

    # 2) Historial reciente como texto (igual que en el 6)
    historial = _historial_como_texto(conv)

    prompt = f"""Eres un asistente de chat con memoria.

Historial reciente de la conversación:
{historial}

Con base en este historial, responde al último mensaje del usuario.
Responde en español, de forma breve y natural.
"""

    # 3) Llamar al modelo
    respuesta = call_llm(prompt)

    # 4) Guardar la respuesta en la memoria y persistirla
    conv.append({"role": "assistant", "content": respuesta})
    _guardar_memoria(conv)

    return respuesta

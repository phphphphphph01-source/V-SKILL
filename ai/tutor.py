from flask import current_app
from ai.gemini import ask_gemini
from ai.fallback import fallback_answer
def tutor(message,context=""):
    result=ask_gemini(current_app.config.get("GEMINI_API_KEY",""),message,context)
    return result or fallback_answer(message,context)

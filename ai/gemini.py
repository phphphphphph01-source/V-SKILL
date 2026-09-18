def ask_gemini(api_key, message, context=""):
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model=genai.GenerativeModel("gemini-1.5-flash")
        prompt=f"""You are V-SKILL Tutor. Do not reveal an assessment answer immediately.
Give a concise hint or explanation appropriate to the student's context.
Message: {message}
Context: {context}"""
        r=model.generate_content(prompt)
        return {"provider":"gemini","answer":r.text,"hint_level":1}
    except Exception:
        return None

def translate(text: str, target_lang: str) -> str:
    # Dummy translation mapping.
    translations = {
        ("hello", "es"): "hola",
        ("goodbye", "es"): "adiós"
    }
    return translations.get((text.lower(), target_lang.lower()), text)

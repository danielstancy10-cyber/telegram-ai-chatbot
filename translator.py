from deep_translator import GoogleTranslator

LANGUAGES = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Arabic": "ar",
    "Yoruba": "yo",
    "Hausa": "ha",
    "Igbo": "ig"
}


def translate(text, language):
    code = LANGUAGES.get(language, "en")

    if code == "en":
        return text

    return GoogleTranslator(source="auto", target=code).translate(text)
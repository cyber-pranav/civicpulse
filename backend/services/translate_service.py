"""
@module TranslateService
@description Translates UI text using Google Cloud Translation API.
"""
from google.cloud import translate_v2 as translate
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

_client = None

def _get_client():
    global _client
    if _client is None:
        try:
            _client = translate.Client()
        except Exception as e:
            Logger.error(f"TranslateService init failed: {e}")
    return _client

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali",
    "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "pa": "Punjabi"
}

async def translate_texts(texts: list[str], target_language: str) -> list[str]:
    """
    @description Translates a list of UI strings to the target language.
    @param texts: list[str] - Strings to translate
    @param target_language: str - ISO 639-1 language code
    @returns list[str] - Translated strings in same order
    """
    if target_language not in SUPPORTED_LANGUAGES:
        return texts
    if target_language == "en":
        return texts
    cache_key = f"translate_{target_language}_{hash(tuple(texts))}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        client = _get_client()
        if not client:
            raise Exception("Translate Client not initialized")
        results = client.translate(texts, target_language=target_language)
        translated = [r["translatedText"] for r in results]
        cache_set(cache_key, translated, ttl=86400)
        return translated
    except Exception as e:
        Logger.error(f"TranslateService.translate_texts failed: {e}")
        return texts

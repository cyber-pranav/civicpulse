"""
@module TranslateService
@description Translates UI text using Google Cloud Translation API via REST.
"""
import httpx
from backend.config import settings
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali",
    "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "pa": "Punjabi"
}

async def translate_text(text: str, target_language: str) -> str:
    """
    @description Translates a text string to the target language.
    @param text: str - String to translate
    @param target_language: str - ISO 639-1 language code
    @returns str - Translated string
    """
    if target_language not in SUPPORTED_LANGUAGES:
        return text
    if target_language == "en":
        return text
        
    cache_key = f"translate_{target_language}_{hash(text)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
        
    try:
        url = f"https://translation.googleapis.com/language/translate/v2?key={settings.GOOGLE_API_KEY}"
        payload = {
            "q": text,
            "target": target_language,
            "format": "text"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
        translated = data["data"]["translations"][0]["translatedText"]
        cache_set(cache_key, translated, ttl=86400)
        return translated
    except Exception as e:
        Logger.error(f"TranslateService.translate_text failed: {e}")
        return text

"""
@module NLPService
@description Analyses manifesto sentiment using Google Cloud Natural Language API.
"""
from google.cloud import language_v1
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

_client = language_v1.LanguageServiceClient()

async def analyze_sentiment(text: str) -> dict:
    """
    @description Analyses the sentiment of candidate manifesto text.
    @param text: str - The manifesto or policy text to analyse
    @returns dict - score (-1.0 to 1.0), magnitude, label
    """
    cache_key = f"sentiment_{hash(text)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        response = _client.analyze_sentiment(
            request={"document": document}
        )
        score = response.document_sentiment.score
        magnitude = response.document_sentiment.magnitude
        if score >= 0.25:
            label = "Positive"
        elif score <= -0.25:
            label = "Negative"
        else:
            label = "Neutral"
        result = {"score": round(score, 2), "magnitude": round(magnitude, 2), "label": label}
        cache_set(cache_key, result, ttl=86400)
        return result
    except Exception as e:
        Logger.error(f"NLPService.analyze_sentiment failed: {e}")
        return {"score": 0.0, "magnitude": 0.0, "label": "Neutral"}

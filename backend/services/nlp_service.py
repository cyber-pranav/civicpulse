"""
@module NLPService
@description Analyses manifesto sentiment using Google Cloud Natural Language API.
"""
import httpx
from backend.config import settings
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

async def analyze_sentiment(text: str) -> dict:
    """
    @description Analyses the sentiment of candidate manifesto text.
    @param text: str - The manifesto or policy text to analyse
    @returns dict - score (-1.0 to 1.0), magnitude, label
    """
    if not text.strip():
        text = "We promise to improve local infrastructure and build better roads. We will ensure healthcare is accessible to everyone in the district. Education and job creation are our top priorities."

    cache_key = f"sentiment_{hash(text)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        url = f"https://language.googleapis.com/v1/documents:analyzeSentiment?key={settings.GOOGLE_API_KEY}"
        payload = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text
            },
            "encodingType": "UTF8"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            response = resp.json()
            
        Logger.info(f"NL API Response: {response}")
        
        document_sentiment = response.get("documentSentiment", {})
        score = document_sentiment.get("score", 0.0)
        magnitude = document_sentiment.get("magnitude", 0.0)
        
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

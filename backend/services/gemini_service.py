"""
@module GeminiService
@description Handles all Gemini 1.5 Flash AI interactions including
             candidate analysis, intelligent search, and civic Q&A.
"""
import google.generativeai as genai
from backend.config import settings
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")

CIVIC_SYSTEM_PROMPT = """You are CivicPulse AI, an expert on Indian elections,
the Election Commission of India, EVM machines, voter registration (EPIC/Voter ID),
election timelines, constituencies, NOTA, Model Code of Conduct, and the democratic
process. Answer only civic and election-related questions concisely and accurately.
For unrelated questions, politely redirect to election topics."""

async def analyze_candidate(candidate_name: str, manifesto: str) -> dict:
    """
    @description Analyzes a candidate's manifesto using Gemini AI.
    @param candidate_name: str - The candidate's full name
    @param manifesto: str - The candidate's manifesto text
    @returns dict - Analysis with tone, topTopics, voterAppeal, redFlags
    """
    cache_key = f"candidate_analysis_{hash(manifesto)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        prompt = f"""Analyze this Indian election candidate's manifesto.
Candidate: {candidate_name}
Manifesto: {manifesto}

Return ONLY a JSON object (no markdown, no explanation) with these exact fields:
{{
  "tone": "Positive" or "Neutral" or "Critical",
  "topTopics": ["topic1", "topic2", "topic3"],
  "voterAppeal": "one sentence summary",
  "redFlags": ["concern1"] or []
}}"""
        response = await _model.generate_content_async(prompt)
        import json
        result = json.loads(response.text.strip())
        cache_set(cache_key, result, ttl=3600)
        return result
    except Exception as e:
        Logger.error(f"GeminiService.analyze_candidate failed: {e}")
        return {"tone": "Neutral", "topTopics": [], "voterAppeal": "Analysis unavailable.", "redFlags": []}

async def answer_civic_question(question: str, history: list) -> str:
    """
    @description Answers a civic/election question using Gemini with conversation history.
    @param question: str - The user's question
    @param history: list - Previous conversation turns
    @returns str - Gemini's answer
    """
    try:
        chat = _model.start_chat(history=history)
        full_prompt = f"{CIVIC_SYSTEM_PROMPT}\n\nUser question: {question}"
        response = await chat.send_message_async(full_prompt)
        return response.text
    except Exception as e:
        Logger.error(f"GeminiService.answer_civic_question failed: {e}")
        return "I'm unable to answer right now. Please try again in a moment."

async def search_candidates(query: str, candidates: list) -> list:
    """
    @description Uses Gemini to intelligently filter candidates by search query.
    @param query: str - User's natural language search query
    @param candidates: list - List of candidate dicts with id, name, party, topics
    @returns list - Filtered list of matching candidate IDs
    """
    cache_key = f"search_{hash(query)}_{len(candidates)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        import json
        prompt = f"""Search query: "{query}"
Candidates: {json.dumps(candidates)}
Return ONLY a JSON array of matching candidate IDs based on name, party, or policy topics. Example: ["id1","id2"]"""
        response = await _model.generate_content_async(prompt)
        result = json.loads(response.text.strip())
        cache_set(cache_key, result, ttl=300)
        return result
    except Exception as e:
        Logger.error(f"GeminiService.search_candidates failed: {e}")
        return [c["id"] for c in candidates]

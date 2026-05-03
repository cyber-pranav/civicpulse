"""
@module FirebaseService
@description Manages Firebase Admin SDK for Firestore user progress
             persistence and Firebase Auth token verification.
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth
from backend.config import settings
from backend.utils.logger import Logger

_db = None

def _initialize():
    """
    @description Initializes Firebase Admin SDK once.
    @returns None
    """
    global _db
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            _db = firestore.client()
            Logger.info("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            Logger.error(f"FirebaseService._initialize failed: {e}")
            _db = None

_initialize()

async def save_user_progress(user_id: str, progress: dict) -> bool:
    """
    @description Saves user journey progress to Firestore.
    @param user_id: str - Firebase Auth UID
    @param progress: dict - Journey progress state
    @returns bool - True on success, False on failure
    """
    if not _db:
        return False
    try:
        _db.collection("userProgress").document(user_id).set(
            progress, merge=True
        )
        return True
    except Exception as e:
        Logger.error(f"FirebaseService.save_user_progress failed: {e}")
        return False

async def load_user_progress(user_id: str) -> dict:
    """
    @description Loads user journey progress from Firestore.
    @param user_id: str - Firebase Auth UID
    @returns dict - Saved progress or empty dict
    """
    if not _db:
        return {}
    try:
        doc = _db.collection("userProgress").document(user_id).get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        Logger.error(f"FirebaseService.load_user_progress failed: {e}")
        return {}

async def verify_token(id_token: str) -> dict | None:
    """
    @description Verifies a Firebase Auth ID token.
    @param id_token: str - The JWT token from the frontend
    @returns dict - Decoded token claims, or None if invalid
    """
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        Logger.error(f"FirebaseService.verify_token failed: {e}")
        return None

import firebase_admin
from firebase_admin import auth
from app.core.config import settings
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)



from app.core.firebase import init_firebase
init_firebase()

security = HTTPBearer()

async def verify_firebase_token(cred: HTTPAuthorizationCredentials) -> dict:
    """Verifies a Firebase JWT and returns the decoded token payload."""
    
    token = cred.credentials
    if token.startswith("Bearer "):
        token = token[7:]
        
    if getattr(settings, "ENVIRONMENT", "production") == "local" and "mock-" in token:
        email = token.replace("mock-", "")
        logger.info(f"Using mock token bypass for email: {email}")
        return {"email": email, "name": "Mock User"}

    try:
        # Use the stripped token (without 'Bearer ' prefix)
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

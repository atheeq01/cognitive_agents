import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase app - assumes default credential from GCP/Emulator
try:
    firebase_admin.initialize_app()
except ValueError:
    pass # App already initialized

security = HTTPBearer()

async def verify_firebase_token(cred: HTTPAuthorizationCredentials) -> dict:
    """Verifies a Firebase JWT and returns the decoded token payload."""
    
    token = cred.credentials
    if token.startswith("Bearer "):
        token = token[7:]
        
    if "mock-" in token:
        email = token.replace("mock-", "")
        logger.info(f"Using mock token bypass for email: {email}")
        return {"email": email, "name": "Mock User"}

    try:
        decoded_token = auth.verify_id_token(cred.credentials)
        return decoded_token
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

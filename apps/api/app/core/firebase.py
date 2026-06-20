import firebase_admin
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_firebase():
    try:
        if not firebase_admin._apps:
            project_id = getattr(settings, "FIREBASE_PROJECT_ID", os.environ.get("FIREBASE_PROJECT_ID", "omnimind-499716"))
            if project_id:
                firebase_admin.initialize_app(options={"projectId": project_id})
            else:
                firebase_admin.initialize_app()
    except ValueError:
        pass
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")

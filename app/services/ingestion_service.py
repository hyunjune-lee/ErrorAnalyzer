import json
import os
import logging
from typing import List, Dict, Any
from app.config import settings
from app.services.nelo_client import NeloClient

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

def fetch_logs(db: Session) -> List[Dict[str, Any]]:
    """로그 소스 타입에 따라 적절한 방법으로 로그를 가져옵니다."""
    
    if settings.log_source_type.lower() == "nelo":
        logger.info("Fetching logs from NELO API")
        return fetch_from_nelo(db)
    else:
        logger.warning(f"Log source type is set to '{settings.log_source_type}', but only 'nelo' is supported now.")
        return []

def fetch_from_nelo(db: Session) -> List[Dict[str, Any]]:
    """NELO API에서 로그를 가져옵니다."""
    try:
        nelo_client = NeloClient()
        logs = nelo_client.fetch_error_logs(db, minutes_back=360)  # 6시간으로 확장
        logger.info(f"Fetched {len(logs)} logs from NELO")
        return logs
    except Exception as e:
        logger.error(f"Error fetching from NELO: {e}")
        return []

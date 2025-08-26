import json
import os
import logging
from typing import List, Dict, Any
from app.config import settings
from app.services.nelo_client import NeloClient

logger = logging.getLogger(__name__)

def fetch_logs() -> List[Dict[str, Any]]:
    """로그 소스 타입에 따라 적절한 방법으로 로그를 가져옵니다."""
    
    if settings.log_source_type.lower() == "nelo":
        logger.info("Fetching logs from NELO API")
        return fetch_from_nelo()
    else:
        logger.info("Fetching logs from file")
        return fetch_from_file()

def fetch_from_nelo() -> List[Dict[str, Any]]:
    """NELO API에서 로그를 가져옵니다."""
    try:
        nelo_client = NeloClient()
        logs = nelo_client.fetch_error_logs(minutes_back=360)  # 6시간으로 확장
        logger.info(f"Fetched {len(logs)} logs from NELO")
        return logs
    except Exception as e:
        logger.error(f"Error fetching from NELO: {e}")
        logger.info("Falling back to sample logs")
        return fetch_from_file()

def fetch_from_file() -> List[Dict[str, Any]]:
    """파일에서 로그를 가져옵니다."""
    try:
        if not os.path.exists(settings.log_source_path):
            logger.warning(f"Log source file not found: {settings.log_source_path}")
            return []
        
        with open(settings.log_source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'logs' in data:
            return data['logs']
        else:
            logger.error("Invalid log file format. Expected list or object with 'logs' key.")
            return []
    
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return []
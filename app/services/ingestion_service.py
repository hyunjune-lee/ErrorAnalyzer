import json
import os
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def fetch_logs() -> List[Dict[str, Any]]:
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
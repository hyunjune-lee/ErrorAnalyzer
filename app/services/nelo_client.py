import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class NeloClient:
    def __init__(self):
        self.api_url = settings.nelo_api_url
        self.access_key = settings.nelo_access_key
        self.secret_key = settings.nelo_secret_key
        self.group_id = settings.nelo_group_id

        if not self.access_key or not self.secret_key:
            logger.warning("NELO API keys not configured. Using sample logs instead.")

    def get_headers(self) -> Dict[str, str]:
        return {
            "X-NELO-ACCESS-KEY-ID": self.access_key,
            "X-NELO-SECRET-ACCESS-KEY": self.secret_key,
            "Content-Type": "application/json"
        }

    def fetch_error_logs(self, minutes_back: int = 5) -> List[Dict[str, Any]]:
        """NELO API에서 최근 에러 로그들을 가져옵니다."""
        if not self.access_key or not self.secret_key:
            logger.warning("NELO credentials not available, using Mock client")
            return self._use_mock_client(minutes_back)

        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes_back)

            # Unix timestamp in milliseconds
            from_time = int(start_time.timestamp() * 1000)
            to_time = int(end_time.timestamp() * 1000)

            params = {
                "dataSource.groupId": self.group_id,
                "query": "logLevel:ERROR",
                "fields": "logTime,logLevel,body,Location,clientIp,host,userId,projectName,url,requestId,logType,Exception,errorCode,Referrer",
                "format": "json",
                "count": "100",
                "limit": "100",
                "compression": "false",
                "from": from_time,
                "to": to_time
            }

            logger.info(f"Fetching NELO logs for group {self.group_id} from {start_time} to {end_time}")

            response = requests.get(
                self.api_url,
                headers=self.get_headers(),
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                logs = response.json()
                logger.info(f"Successfully fetched {len(logs)} logs from NELO")
                return self.normalize_nelo_logs(logs)
            elif response.status_code == 401:
                logger.error(f"NELO API authentication failed: {response.text}")
                logger.info("Falling back to Mock NELO client")
                return self._use_mock_client(minutes_back)
            else:
                logger.error(f"NELO API error: {response.status_code} - {response.text}")
                logger.info("Falling back to Mock NELO client")
                return self._use_mock_client(minutes_back)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching NELO logs: {e}")
            logger.info("Falling back to Mock NELO client")
            return self._use_mock_client(minutes_back)
        except Exception as e:
            logger.error(f"Unexpected error while fetching NELO logs: {e}")
            logger.info("Falling back to Mock NELO client")
            return self._use_mock_client(minutes_back)

    def normalize_nelo_logs(self, nelo_logs: List[Dict]) -> List[Dict[str, Any]]:
        """NELO 로그 포맷을 내부 포맷으로 변환합니다."""
        normalized_logs = []

        for log in nelo_logs:
            try:
                normalized_log = {
                    "timestamp": log.get("logTime", datetime.now().isoformat()),
                    "logLevel": log.get("logLevel", "ERROR"),
                    "logger": log.get("Location", "unknown.logger"),
                    "application": log.get("projectName", "Unknown-App"),
                    "projectName": log.get("projectName", "NELO-Project"),
                    "body": log.get("body", ""),
                    "metadata": {
                        "clientIp": log.get("clientIp"),
                        "host": log.get("host"),
                        "userId": log.get("userId"),
                        "url": log.get("url"),
                        "requestId": log.get("requestId"),
                        "logType": log.get("logType"),
                        "errorCode": log.get("errorCode"),
                        "referrer": log.get("Referrer")
                    }
                }

                # Exception 필드가 있으면 stackTrace로 처리
                if log.get("Exception"):
                    exception_text = log.get("Exception")
                    if isinstance(exception_text, str):
                        # 스택트레이스를 줄 단위로 분리
                        stack_lines = [line.strip() for line in exception_text.split('\n') if line.strip()]
                        normalized_log["stackTrace"] = stack_lines

                normalized_logs.append(normalized_log)

            except Exception as e:
                logger.warning(f"Failed to normalize NELO log: {e}")
                continue

        logger.info(f"Normalized {len(normalized_logs)} NELO logs")
        return normalized_logs

    def _use_mock_client(self, minutes_back: int) -> List[Dict[str, Any]]:
        """Mock NELO 클라이언트를 사용합니다."""
        try:
            from app.services.mock_nelo_client import MockNeloClient
            mock_client = MockNeloClient()
            return mock_client.fetch_error_logs(minutes_back)
        except ImportError:
            logger.error("Mock NELO client not available")
            return []

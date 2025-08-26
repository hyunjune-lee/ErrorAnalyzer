import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

logger = logging.getLogger(__name__)

class MockNeloClient:
    """NELO API 키가 유효하지 않을 때 사용하는 Mock 클라이언트"""
    
    def __init__(self):
        self.group_id = "6370"
        logger.info("Using Mock NELO Client for testing")
    
    def fetch_error_logs(self, minutes_back: int = 5) -> List[Dict[str, Any]]:
        """Mock NELO 로그를 생성합니다."""
        logger.info(f"Mock NELO: Generating sample logs for the last {minutes_back} minutes")
        
        # 실제 NELO에서 가져올 수 있는 로그 샘플 생성
        mock_logs = []
        
        base_time = datetime.now()
        
        # 다양한 타입의 에러 로그 샘플 생성
        error_samples = [
            {
                "body": "java.lang.NullPointerException: Cannot invoke method on null object",
                "Location": "com.naver.chat.service.MessageService.sendMessage:124",
                "projectName": "OpenChat-API",
                "logLevel": "ERROR",
                "Exception": "java.lang.NullPointerException\n\tat com.naver.chat.service.MessageService.sendMessage(MessageService.java:124)\n\tat com.naver.chat.controller.MessageController.send(MessageController.java:45)"
            },
            {
                "body": "Database connection timeout after 30000ms",
                "Location": "com.naver.chat.database.ConnectionPool.getConnection:89",
                "projectName": "OpenChat-API", 
                "logLevel": "ERROR",
                "Exception": "java.sql.SQLException: Connection timeout\n\tat com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:181)"
            },
            {
                "body": "Redis connection lost - attempting reconnection",
                "Location": "com.naver.chat.cache.RedisClient.connect:67",
                "projectName": "OpenChat-Cache",
                "logLevel": "WARN"
            },
            {
                "body": "Failed to process chat message - invalid user ID",
                "Location": "com.naver.chat.service.ChatService.processMessage:156", 
                "projectName": "OpenChat-API",
                "logLevel": "ERROR",
                "Exception": "com.naver.chat.exception.InvalidUserException: User ID cannot be null or empty\n\tat com.naver.chat.service.ChatService.validateUser(ChatService.java:203)"
            },
            {
                "body": "Rate limit exceeded for user requests",
                "Location": "com.naver.chat.filter.RateLimitFilter.doFilter:78",
                "projectName": "OpenChat-Gateway",
                "logLevel": "WARN"
            }
        ]
        
        # 랜덤하게 1-10개의 로그 생성
        num_logs = random.randint(1, 10)
        
        for i in range(num_logs):
            sample = random.choice(error_samples)
            
            # 시간을 최근 범위로 랜덤 설정
            log_time = base_time - timedelta(
                minutes=random.randint(0, minutes_back),
                seconds=random.randint(0, 59)
            )
            
            mock_log = {
                "logTime": log_time.isoformat() + "Z",
                "logLevel": sample["logLevel"],
                "body": sample["body"],
                "Location": sample["Location"],
                "projectName": sample["projectName"],
                "clientIp": f"10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "host": f"openchat-{random.choice(['api', 'cache', 'gateway'])}-{random.randint(1,10)}",
                "userId": f"user_{random.randint(100000, 999999)}",
                "url": f"/api/v1/{random.choice(['messages', 'users', 'rooms'])}/{random.randint(1, 1000)}",
                "requestId": f"req_{random.randint(100000000, 999999999)}",
                "logType": "application"
            }
            
            # Exception이 있으면 추가
            if "Exception" in sample:
                mock_log["Exception"] = sample["Exception"]
            
            mock_logs.append(mock_log)
        
        # NELO 포맷을 내부 포맷으로 변환
        normalized_logs = self.normalize_nelo_logs(mock_logs)
        
        logger.info(f"Mock NELO: Generated {len(normalized_logs)} sample logs")
        return normalized_logs
    
    def normalize_nelo_logs(self, nelo_logs: List[Dict]) -> List[Dict[str, Any]]:
        """NELO 로그 포맷을 내부 포맷으로 변환합니다."""
        normalized_logs = []
        
        for log in nelo_logs:
            try:
                normalized_log = {
                    "timestamp": log.get("logTime", datetime.now().isoformat()),
                    "logLevel": log.get("logLevel", "ERROR"),
                    "logger": log.get("Location", "unknown.logger"),
                    "application": log.get("projectName", "Mock-App"),
                    "projectName": log.get("projectName", "Mock-Project"),
                    "body": log.get("body", ""),
                    "metadata": {
                        "clientIp": log.get("clientIp"),
                        "host": log.get("host"),
                        "userId": log.get("userId"),
                        "url": log.get("url"),
                        "requestId": log.get("requestId"),
                        "logType": log.get("logType")
                    }
                }
                
                # Exception 필드가 있으면 stackTrace로 처리
                if log.get("Exception"):
                    exception_text = log.get("Exception")
                    if isinstance(exception_text, str):
                        stack_lines = [line.strip() for line in exception_text.split('\n') if line.strip()]
                        normalized_log["stackTrace"] = stack_lines
                
                normalized_logs.append(normalized_log)
                
            except Exception as e:
                logger.warning(f"Failed to normalize mock NELO log: {e}")
                continue
        
        return normalized_logs
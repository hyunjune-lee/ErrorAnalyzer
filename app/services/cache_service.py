from typing import Set
from sqlalchemy.orm import Session
from app.database.models import ErrorGroup, GroupStatus

class AppCacheService:
    def __init__(self):
        self.non_issue_fingerprints: Set[str] = set()
    
    def initialize(self, db: Session):
        non_issues = db.query(ErrorGroup).filter(ErrorGroup.status == GroupStatus.NON_ISSUE).all()
        self.non_issue_fingerprints = {group.fingerprint for group in non_issues}
    
    def is_non_issue(self, fingerprint: str) -> bool:
        return fingerprint in self.non_issue_fingerprints

app_cache = AppCacheService()
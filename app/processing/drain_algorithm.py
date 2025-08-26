import re
import hashlib
from typing import Dict, List, Set, Optional

class DrainNode:
    def __init__(self):
        self.log_template_tokens = []
        self.log_ids = []
        
class DrainParser:
    def __init__(self, depth=4, similarity_threshold=0.6, max_children=100):
        self.depth = depth
        self.similarity_threshold = similarity_threshold
        self.max_children = max_children
        self.templates = []  # 모든 템플릿을 저장하는 리스트
        self.logmessage_tokens = {}
        
    def normalize_message(self, content: str) -> str:
        # Channel IDs (N1wWoR, N1xBOV 등)
        content = re.sub(r'\bN[0-9a-zA-Z_]+\b', '<CHANNEL_ID>', content)
        
        # Profile IDs (01K1Z8Z1ZSN4RABANBBM0TB00W 형태)
        content = re.sub(r'ProfileId\[value=[0-9A-Z]+\]', 'ProfileId[value=<PROFILE_ID>]', content)
        content = re.sub(r'\b[0-9A-Z]{26}\b', '<PROFILE_ID>', content)
        
        # Request IDs, Session IDs 등
        content = re.sub(r'\breq_\d+\b', '<REQ_ID>', content)
        content = re.sub(r'\bsession_[a-zA-Z0-9]+\b', '<SESSION_ID>', content)
        
        # 기본 패턴들
        content = re.sub(r'\b\d+\b', '<NUM>', content)
        content = re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '<UUID>', content)
        content = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', content)
        content = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '<EMAIL>', content)
        content = re.sub(r'\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b', '<URL>', content)
        content = re.sub(r'\b/[/\w.-]*\b', '<PATH>', content)
        
        # 타임스탬프 패턴
        content = re.sub(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*Z?\b', '<TIMESTAMP>', content)
        
        # 문자열 패턴
        content = re.sub(r"'[^']*'", '<STR>', content)
        content = re.sub(r'"[^"]*"', '<STR>', content)
        
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    
    def add_log_message(self, log_message: str) -> str:
        normalized = self.normalize_message(log_message)
        tokens = normalized.split()
        
        if len(tokens) < 2:
            return normalized
            
        template_candidate = self._search_template(tokens)
        if template_candidate:
            return ' '.join(template_candidate.log_template_tokens)
        else:
            new_template = DrainNode()
            new_template.log_template_tokens = tokens
            self.templates.append(new_template)  # 새 템플릿을 리스트에 추가
            return ' '.join(tokens)
    
    def _search_template(self, tokens: List[str]) -> Optional[DrainNode]:
        for template in self._get_all_templates():
            if self._similarity(tokens, template.log_template_tokens) >= self.similarity_threshold:
                self._update_template(template, tokens)
                return template
        return None
    
    def _get_all_templates(self) -> List[DrainNode]:
        return self.templates
    
    def _similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        # 길이가 다른 경우에도 유사도 계산 개선
        if not tokens1 or not tokens2:
            return 0.0
        
        # 더 짧은 길이를 기준으로 비교
        min_len = min(len(tokens1), len(tokens2))
        if min_len == 0:
            return 0.0
            
        # 앞부분 토큰들의 유사도 계산
        matches = sum(1 for i in range(min_len) if tokens1[i] == tokens2[i])
        base_similarity = matches / min_len
        
        # 길이 차이에 대한 페널티 (최대 0.3까지 감소)
        max_len = max(len(tokens1), len(tokens2))
        length_penalty = min(0.3, abs(len(tokens1) - len(tokens2)) / max_len)
        
        return max(0.0, base_similarity - length_penalty)
    
    def _update_template(self, template: DrainNode, tokens: List[str]):
        # 더 긴 길이에 맞춰서 템플릿 업데이트
        max_len = max(len(template.log_template_tokens), len(tokens))
        new_template = []
        
        for i in range(max_len):
            t1 = template.log_template_tokens[i] if i < len(template.log_template_tokens) else '<*>'
            t2 = tokens[i] if i < len(tokens) else '<*>'
            
            if t1 == t2:
                new_template.append(t1)
            else:
                new_template.append('<*>')
        
        template.log_template_tokens = new_template
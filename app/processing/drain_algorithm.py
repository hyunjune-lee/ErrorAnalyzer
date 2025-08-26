import re
import hashlib
from typing import Dict, List, Set, Optional

class DrainNode:
    def __init__(self):
        self.log_template_tokens = []
        self.log_ids = []
        
class DrainParser:
    def __init__(self, depth=4, similarity_threshold=0.4, max_children=100):
        self.depth = depth
        self.similarity_threshold = similarity_threshold
        self.max_children = max_children
        self.root_node = DrainNode()
        self.logmessage_tokens = {}
        
    def normalize_message(self, content: str) -> str:
        content = re.sub(r'\b\d+\b', '<NUM>', content)
        content = re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '<UUID>', content)
        content = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', content)
        content = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '<EMAIL>', content)
        content = re.sub(r'\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b', '<URL>', content)
        content = re.sub(r'\b/[/\w.-]*\b', '<PATH>', content)
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
            return ' '.join(tokens)
    
    def _search_template(self, tokens: List[str]) -> Optional[DrainNode]:
        for template in self._get_all_templates():
            if self._similarity(tokens, template.log_template_tokens) >= self.similarity_threshold:
                self._update_template(template, tokens)
                return template
        return None
    
    def _get_all_templates(self) -> List[DrainNode]:
        return [self.root_node]
    
    def _similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        if len(tokens1) != len(tokens2):
            return 0.0
        
        matches = sum(1 for t1, t2 in zip(tokens1, tokens2) if t1 == t2)
        return matches / len(tokens1) if tokens1 else 0.0
    
    def _update_template(self, template: DrainNode, tokens: List[str]):
        new_template = []
        for i, (t1, t2) in enumerate(zip(template.log_template_tokens, tokens)):
            if t1 == t2:
                new_template.append(t1)
            else:
                new_template.append('<*>')
        template.log_template_tokens = new_template
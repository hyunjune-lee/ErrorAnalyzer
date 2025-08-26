import hashlib
import re
from typing import Tuple, Optional, Dict, Any
from app.processing.drain_algorithm import DrainParser

drain_parser = DrainParser()

def normalize_stacktrace(stacktrace: str) -> str:
    lines = []
    for line in stacktrace.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        line = re.sub(r':\d+', ':<LINE>', line)
        line = re.sub(r'\$\d+', '$<NUM>', line)
        line = re.sub(r'\.java:\d+', '.java:<LINE>', line)
        line = re.sub(r'\([^)]*\.java:\d+\)', '(<CLASS>.java:<LINE>)', line)
        line = re.sub(r'\b\d+\b', '<NUM>', line)
        
        lines.append(line)
    
    return '\n'.join(lines[:10])

def extract_exception_signature(log_data: Dict[str, Any]) -> Optional[str]:
    if 'stackTrace' in log_data and log_data['stackTrace']:
        stacktrace = log_data['stackTrace']
        if isinstance(stacktrace, list):
            stacktrace = '\n'.join(stacktrace)
        
        normalized = normalize_stacktrace(stacktrace)
        return normalized
    
    if 'body' in log_data:
        body = log_data['body']
        exception_patterns = [
            r'(java\.[\w.]+Exception)',
            r'([\w.]*Exception)',
            r'([\w.]*Error)',
            r'(org\.[\w.]+\.[\w]+Exception)'
        ]
        
        for pattern in exception_patterns:
            match = re.search(pattern, body)
            if match:
                return match.group(1)
    
    return None

def generate_drain_template(log_data: Dict[str, Any]) -> str:
    message = ""
    
    if 'body' in log_data:
        message = log_data['body']
    elif 'message' in log_data:
        message = log_data['message']
    
    if 'logLevel' in log_data:
        message = f"[{log_data['logLevel']}] {message}"
    
    template = drain_parser.add_log_message(message)
    return template

def generate_hybrid_fingerprint(log_data: Dict[str, Any]) -> Tuple[str, str, str]:
    exception_sig = extract_exception_signature(log_data)
    
    if exception_sig:
        fingerprint = hashlib.sha256(exception_sig.encode()).hexdigest()[:16]
        return f"stk_{fingerprint}", "STACKTRACE", exception_sig
    
    drain_template = generate_drain_template(log_data)
    fingerprint = hashlib.sha256(drain_template.encode()).hexdigest()[:16]
    return f"drn_{fingerprint}", "DRAIN", drain_template
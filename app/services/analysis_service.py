import requests
import json
import logging
import re
from app.config import settings
from app.database.models import ErrorGroup, AnalysisReport, GroupStatus
from app.database.connection import get_new_db_session

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
당신은 전문적인 Java 백엔드 개발자이자 DevOps 엔지니어입니다.
애플리케이션 '{application}'에서 새로운 유형의 에러가 감지되었습니다.
제공된 에러 정보와 샘플 로그를 분석하여 실행 가능한 인사이트를 제공해주세요.

[에러 정보 요약]
Logger: {logger_name}
에러 시그니처 (정규화됨):
{signature}

[샘플 로그 전문 (참고용)]
```json
{sample_log_json}
```

[분석 요청 사항]
반드시 아래 JSON 형식으로만 응답해주세요. 다른 설명은 절대 포함하지 마세요.
{{
"summary": "에러 내용 요약 (50자 이내)",
"root_cause": "에러가 발생한 기술적 근본 원인 상세 설명",
"impact_analysis": "이 에러로 인해 예상되는 시스템 또는 사용자 영향",
"solution": ["해결 방안 또는 디버깅 가이드 (단계별 배열)"],
"tags": ["핵심 키워드 태그 배열 (예: Kafka, SSL, Infra)"],
"is_transient": "일시적인 문제일 가능성이 높으면 true, 지속적이면 false",
"risk_score": "이 에러의 심각도, 영향 범위, 발생 빈도를 종합적으로 고려한 위험 점수 (0~100 사이 정수)"
}}
"""

def _call_ai_api(prompt: str) -> str:
    """실제 AI API 호출 (현재는 더미 응답이므로 예외 발생시켜 fallback 사용)"""
    # TODO: 실제 AI API 구현 (OpenAI, Claude 등)
    # if settings.ai_api_key and settings.ai_api_url:
    #     response = requests.post(settings.ai_api_url, ...)
    #     return response.json()
    
    logger.info("AI API not configured, will use fallback analysis")
    raise Exception("AI API not configured")

def _parse_ai_response(content: str) -> dict | None:
    if not content: return None
    try:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != 0:
            return json.loads(content[json_start:json_end])
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI response as JSON: {content[:200]}...")
        return None

def analyze_error_with_ai(group_id: int, sample_log: dict):
    logger.info(f"Starting background AI analysis for Group ID: {group_id}")
    db = get_new_db_session()
    try:
        group = db.query(ErrorGroup).filter(ErrorGroup.id == group_id).first()
        if not group or group.status != GroupStatus.ANALYZING:
            return

        prompt = PROMPT_TEMPLATE.format(
            application=sample_log.get("application", "Unknown"),
            logger_name=sample_log.get("logger", "Unknown"),
            signature=group.representative_signature,
            sample_log_json=json.dumps(sample_log, indent=2, ensure_ascii=False)
        )

        # Try AI analysis first
        try:
            response_content = _call_ai_api(prompt)
            analysis_data = _parse_ai_response(response_content)
        except Exception as e:
            logger.warning(f"AI analysis failed for Group ID: {group_id}, using fallback: {e}")
            analysis_data = _generate_fallback_analysis(group.representative_signature, sample_log)

        if analysis_data:
            report = AnalysisReport(
                group_id=group.id,
                summary=analysis_data.get("summary"),
                root_cause=analysis_data.get("root_cause"),
                solution=analysis_data.get("solution", []),
                impact=analysis_data.get("impact_analysis")
            )
            db.add(report)
            
            group.risk_score = analysis_data.get("risk_score", 50)
            group.status = GroupStatus.ANALYZED
            group.tags = analysis_data.get("tags", [])
            logger.info(f"AI Analysis completed successfully for Group ID: {group_id}")
        else:
            group.status = GroupStatus.OPEN
            logger.warning(f"AI Analysis failed for Group ID: {group_id}. Status reverted to OPEN.")
        
        db.commit()

    except Exception as e:
        logger.error(f"Error during background AI analysis: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def _generate_fallback_analysis(signature: str, sample_log: dict) -> dict:
    """AI 분석이 실패했을 때 body나 stacktrace에서 중요 정보 추출"""
    
    # Extract key information from body or stacktrace
    body = sample_log.get('body', '')
    stacktrace = sample_log.get('stackTrace', [])
    logger_name = sample_log.get('logger', 'Unknown')
    
    # Generate summary from signature/body
    summary = _extract_error_summary(signature, body)
    
    # Extract root cause from body or stacktrace
    root_cause = _extract_root_cause(body, stacktrace)
    
    # Generate basic impact analysis
    impact = _generate_basic_impact(body, logger_name)
    
    # Generate basic solution
    solution = _generate_basic_solution(body, stacktrace)
    
    # Calculate risk score based on error type
    risk_score = _calculate_risk_score(body, logger_name)
    
    return {
        "summary": summary,
        "root_cause": root_cause,
        "impact_analysis": impact,
        "solution": solution,
        "risk_score": risk_score,
        "tags": _extract_tags(body, logger_name)
    }

def _extract_error_summary(signature: str, body: str) -> str:
    """에러 시그니처나 body에서 핵심 요약 추출"""
    # Remove log level prefix
    clean_sig = re.sub(r'^\[ERROR\]\s*', '', signature)
    
    # Extract key error patterns
    error_patterns = [
        r'(\w+Exception[^:]*)',
        r'(\w+Error[^:]*)',
        r'(.*?(?:failed|error|exception|invalid|cannot|unable|not found)[^:.,]*)',
        r'^([^-:.,]{1,80})'
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, clean_sig, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Fallback to first part of body
    if body:
        return body[:50].strip() + ("..." if len(body) > 50 else "")
    
    return "Unknown Error"

def _extract_root_cause(body: str, stacktrace: list) -> str:
    """Body나 stacktrace에서 근본 원인 추출"""
    if not body and not stacktrace:
        return "근본 원인을 특정할 수 없습니다. 추가 로그 분석이 필요합니다."
    
    # Common error pattern analysis
    causes = {
        r'empty|null|missing': '필수 데이터가 누락되었습니다.',
        r'connection|timeout|network': '네트워크 연결 또는 타임아웃 문제입니다.',
        r'permission|access|denied': '권한 또는 접근 권한 문제입니다.',
        r'configuration|config|property': '설정 파일 또는 속성 값 문제입니다.',
        r'database|sql|db': '데이터베이스 연결 또는 쿼리 문제입니다.',
        r'file|path|directory': '파일 시스템 또는 경로 문제입니다.',
        r'validation|invalid|format': '입력값 검증 또는 형식 오류입니다.',
        r'memory|heap|space': '메모리 부족 또는 리소스 문제입니다.'
    }
    
    text_to_analyze = f"{body} {' '.join(stacktrace) if stacktrace else ''}"
    
    for pattern, cause in causes.items():
        if re.search(pattern, text_to_analyze, re.IGNORECASE):
            return cause
    
    return f"에러 내용: {body[:100]}..." if body else "스택트레이스 분석 필요"

def _generate_basic_impact(body: str, logger_name: str) -> str:
    """기본적인 영향 분석 생성"""
    high_impact_keywords = ['critical', 'fatal', 'security', 'payment', 'auth', 'login']
    medium_impact_keywords = ['user', 'data', 'process', 'service', 'api']
    
    text_to_analyze = f"{body} {logger_name}".lower()
    
    if any(keyword in text_to_analyze for keyword in high_impact_keywords):
        return "시스템 핵심 기능에 영향을 줄 수 있어 즉시 조치가 필요합니다."
    elif any(keyword in text_to_analyze for keyword in medium_impact_keywords):
        return "사용자 경험이나 데이터 처리에 영향을 줄 수 있습니다."
    else:
        return "시스템 안정성에 경미한 영향을 줄 수 있습니다."

def _generate_basic_solution(body: str, stacktrace: list) -> list:
    """기본적인 해결책 제안"""
    solutions = ["상세 로그를 확인하여 구체적인 원인을 파악합니다."]
    
    text_to_analyze = f"{body} {' '.join(stacktrace) if stacktrace else ''}".lower()
    
    if 'null' in text_to_analyze or 'empty' in text_to_analyze:
        solutions.append("입력 데이터 검증 로직을 강화합니다.")
    if 'connection' in text_to_analyze or 'timeout' in text_to_analyze:
        solutions.append("네트워크 연결 상태 및 타임아웃 설정을 확인합니다.")
    if 'config' in text_to_analyze or 'property' in text_to_analyze:
        solutions.append("설정 파일의 속성값이 올바른지 확인합니다.")
    if 'database' in text_to_analyze or 'sql' in text_to_analyze:
        solutions.append("데이터베이스 연결 상태 및 쿼리를 점검합니다.")
    
    solutions.append("모니터링을 통해 재발 여부를 추적합니다.")
    
    return solutions

def _calculate_risk_score(body: str, logger_name: str) -> int:
    """에러 내용을 바탕으로 위험도 점수 계산"""
    base_score = 50
    text_to_analyze = f"{body} {logger_name}".lower()
    
    # High risk indicators
    if any(keyword in text_to_analyze for keyword in ['critical', 'fatal', 'security', 'auth']):
        base_score += 30
    elif any(keyword in text_to_analyze for keyword in ['error', 'exception', 'failed']):
        base_score += 20
    elif any(keyword in text_to_analyze for keyword in ['warning', 'invalid']):
        base_score += 10
    
    return min(100, max(10, base_score))

def _extract_tags(body: str, logger_name: str) -> list:
    """로그 내용에서 태그 추출"""
    tags = []
    text_to_analyze = f"{body} {logger_name}".lower()
    
    tag_patterns = {
        'Database': ['database', 'sql', 'db', 'query'],
        'Network': ['connection', 'timeout', 'network', 'http'],
        'Security': ['auth', 'permission', 'security', 'access'],
        'Configuration': ['config', 'property', 'setting'],
        'Validation': ['invalid', 'validation', 'format', 'parse'],
        'Performance': ['memory', 'timeout', 'slow', 'performance'],
        'Java': ['exception', 'java', 'spring'],
        'API': ['api', 'rest', 'endpoint', 'controller']
    }
    
    for tag, keywords in tag_patterns.items():
        if any(keyword in text_to_analyze for keyword in keywords):
            tags.append(tag)
    
    return tags[:5]  # Limit to 5 tags
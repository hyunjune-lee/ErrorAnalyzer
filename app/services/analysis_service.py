import requests
import json
import logging
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
    logger.warning("Using DUMMY AI response. Implement _call_ai_api for real analysis.")
    return """
    {
        "summary": "Kafka Producer 생성 실패 (SSL 인증서 파일 누락)",
        "root_cause": "Kafka Producer가 SSL 통신을 위해 필요한 인증서 파일을 찾을 수 없어 'java.nio.file.NoSuchFileException'이 발생했습니다.",
        "impact_analysis": "이벤트 발행이 실패하여 도메인 간 데이터 정합성이 깨질 수 있습니다. (예: 채팅방 멤버 상태 업데이트 누락)",
        "solution": [
            "서버의 /home1/irteam/deploy/ 경로에 ca.crt 파일이 존재하는지 확인합니다.",
            "파일 권한이 애플리케이션 실행 계정에서 읽을 수 있는지 확인합니다.",
            "Kafka 설정에서 SSL 인증서 경로가 올바르게 지정되었는지 확인합니다."
        ],
        "tags": ["Kafka", "SSL", "Infra", "Configuration", "Java"],
        "is_transient": false,
        "risk_score": 95
    }
    """

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

        response_content = _call_ai_api(prompt)
        analysis_data = _parse_ai_response(response_content)

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
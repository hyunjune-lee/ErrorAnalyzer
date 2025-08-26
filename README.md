# 🤖 Error Analyzer PoC

AI 기반 에러 로그 분석 및 그룹화 대시보드

## ✨ 주요 기능

- **자동 에러 그룹화**: 스택 트레이스와 Drain 알고리즘을 이용한 지능적 그룹화
- **AI 기반 분석**: 에러 원인, 영향도, 해결 방안 자동 분석
- **실시간 대시보드**: 위험도 점수, 발생 추이, 필터링 기능
- **파이프라인 모니터링**: 실시간 처리 상태 추적
- **논이슈 관리**: 중요하지 않은 에러 자동 필터링

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 애플리케이션 실행
```bash
python run.py
```

### 3. 대시보드 접속
브라우저에서 http://localhost:8000/ui 로 접속

## 📊 대시보드 사용법

### 파이프라인 상태
- 실시간 파이프라인 진행 상황 모니터링
- 수동 파이프라인 실행 가능
- 자동 실행 주기: 60초

### 에러 그룹 관리
- **Active Issues**: 분석이 필요한 실제 에러들
- **Non-Issues**: 논이슈로 분류된 에러들
- 위험도 점수(0-100)로 우선순위 결정
- 발생 추이 스파크라인으로 트렌드 파악

### 필터링 및 정렬
- 날짜 범위 필터 (1시간, 24시간, 7일 등)
- 프로젝트별 필터링
- 위험도 점수, 최신 발생 시간, 발생 횟수로 정렬

## 🔧 설정

### 환경 변수
`.env.example`을 참고하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

### 로그 소스 설정
기본적으로 `sample_logs.json` 파일을 사용하며, `LOG_SOURCE_PATH` 환경 변수로 변경 가능

### AI API 설정 (선택사항)
현재 더미 응답을 사용하며, 실제 AI API 사용 시:
- `AI_API_URL`: AI API 엔드포인트
- `AI_API_KEY`: API 키

## 📁 프로젝트 구조

```
ErrorAnalyzer/
├── app/
│   ├── database/          # 데이터베이스 모델 및 연결
│   ├── processing/        # 로그 처리 및 핑거프린팅
│   ├── services/          # 비즈니스 로직 서비스
│   ├── ui/               # 프론트엔드 대시보드
│   └── main.py           # FastAPI 애플리케이션
├── sample_logs.json      # 샘플 로그 데이터
├── requirements.txt      # Python 의존성
└── run.py               # 실행 스크립트
```

## 🎯 핵심 동작 원리

1. **로그 수집**: 지정된 소스에서 에러 로그 가져오기
2. **그룹화**: 
   - 스택 트레이스 정규화로 우선 그룹화
   - Drain 알고리즘으로 메시지 템플릿 기반 그룹화
3. **AI 분석**: 새 그룹에 대해 배경에서 AI 분석 실행
4. **대시보드 업데이트**: 실시간으로 결과 반영

## 🛠️ API 엔드포인트

- `GET /api/groups`: 모든 에러 그룹 조회
- `POST /api/groups/{id}/toggle-non-issue`: 논이슈 상태 토글
- `GET /api/pipeline-status`: 파이프라인 상태 조회
- `POST /trigger-pipeline`: 수동 파이프라인 실행

## 🔍 로그 형식

```json
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "logLevel": "ERROR",
    "logger": "com.example.service.MyService",
    "application": "MyApp",
    "projectName": "MyProject",
    "body": "Error message",
    "stackTrace": ["stack trace lines..."],
    "metadata": {...}
}
```

## 📈 확장 계획

- 실제 AI API 연동 (OpenAI, Claude 등)
- 다양한 로그 소스 지원 (Elasticsearch, Fluentd 등)
- 알림 시스템 (Slack, 이메일 등)
- 대시보드 커스터마이제이션
- 성능 최적화 및 스케일링

## 🤝 기여하기

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License.
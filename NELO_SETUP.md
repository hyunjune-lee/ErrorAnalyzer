# 🔧 NELO API 연동 가이드

## 현재 상황 분석

테스트 결과, 제공된 NELO API 키에 문제가 있습니다:

```json
{
  "status": 401,
  "code": 40103, 
  "message": "Token is invalid - accessKey (EOF5CLKHWGLE9HIK299K) does not exist."
}
```

## 🔍 NELO API 키 문제 해결 방법

### 1. NELO 웹 콘솔 접속
- NELO 웹 콘솔에 로그인
- API 키 관리 페이지로 이동

### 2. API 키 상태 확인
- 현재 키 `EOF5CLKHWGLE9HIK299K`가 활성 상태인지 확인
- 만료되었거나 삭제된 경우 새로 생성 필요

### 3. 권한 확인
- Group ID `6370`에 대한 읽기 권한이 있는지 확인
- Download API 사용 권한이 활성화되어 있는지 확인

### 4. 새 API 키 생성 (필요시)
- NELO 콘솔에서 새로운 Access Key/Secret Key 쌍 생성
- 적절한 권한 설정 (Group 6370 읽기 권한 포함)

## 🚀 시스템 작동 확인

현재 **Mock 클라이언트**가 자동으로 작동하여 테스트가 가능합니다:

```bash
# 테스트 실행
python test_nelo_client.py

# 실제 파이프라인 테스트  
python run.py
# 브라우저에서 http://localhost:8000/ui 접속
```

## 🎯 실제 NELO 연동 설정

유효한 API 키를 받으면 `.env` 파일 수정:

```bash
# .env 파일
NELO_ACCESS_KEY=your_new_valid_access_key
NELO_SECRET_KEY=your_new_valid_secret_key
NELO_GROUP_ID=6370
LOG_SOURCE_TYPE=nelo
```

## 📊 Mock vs Real 데이터 비교

### Mock 클라이언트 (현재 상태)
- ✅ OpenChat 관련 실제적인 에러 로그 시뮬레이션
- ✅ 다양한 에러 타입 (NPE, DB timeout, Redis 연결 등)  
- ✅ 랜덤한 발생 패턴으로 리얼리즘 구현
- ✅ 모든 파이프라인 기능 정상 작동

### 실제 NELO 연동 시
- 🔄 Group 6370의 실시간 에러 로그
- 🔄 실제 운영 환경 데이터
- 🔄 정확한 시간/빈도 정보
- 🔄 실제 사용자/시스템 정보

## 🛠️ 디버깅 도구 사용법

### 상세 테스트 실행
```bash
python test_nelo_client.py
```

이 스크립트는 다음을 확인합니다:
- API 키 유효성
- 네트워크 연결 상태  
- 다양한 쿼리 조건 테스트
- 시간 범위별 로그 수집 테스트

### 시스템 상태 확인
```bash
curl http://localhost:8000/api/system-status
```

대시보드에서도 NELO 연결 상태를 실시간 확인 가능합니다:
- 🟢 초록불: 실제 NELO 연결됨
- 🟡 노란불: Mock 클라이언트 사용 중

## 💡 추천 해결 순서

1. **현재 상태 확인**: Mock으로 모든 기능이 정상 작동하는지 테스트
2. **NELO 담당자 문의**: API 키 재발급 또는 권한 문제 해결
3. **새 키 적용**: `.env` 파일 업데이트 후 재시작
4. **실제 연동 확인**: `test_nelo_client.py`로 검증

현재는 Mock 데이터로도 충분히 시스템의 모든 기능을 데모하고 테스트할 수 있습니다! 🎉
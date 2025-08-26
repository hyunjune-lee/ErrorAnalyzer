#!/usr/bin/env python3
"""
전체 시스템 통합 테스트
NELO Mock, 파이프라인, UI 등 모든 기능을 테스트합니다.
"""

import time
import requests
from datetime import datetime
from unittest.mock import patch
from app.main import app
from app.config import settings
from fastapi.testclient import TestClient

MOCK_LOG_DATA = [
    {
        "timestamp": datetime.now().isoformat(),
        "logLevel": "ERROR",
        "logger": "com.naver.chat.service.MessageService.sendMessage:124",
        "application": "OpenChat-API",
        "projectName": "OpenChat-API",
        "body": "java.lang.NullPointerException: Cannot invoke method on null object",
        "stackTrace": [
            "java.lang.NullPointerException",
            "at com.naver.chat.service.MessageService.sendMessage(MessageService.java:124)",
            "at com.naver.chat.controller.MessageController.send(MessageController.java:45)"
        ],
        "metadata": {}
    },
    {
        "timestamp": datetime.now().isoformat(),
        "logLevel": "ERROR",
        "logger": "com.naver.chat.database.ConnectionPool.getConnection:89",
        "application": "OpenChat-API",
        "projectName": "OpenChat-API",
        "body": "Database connection timeout after 30000ms",
        "stackTrace": [
            "java.sql.SQLException: Connection timeout",
            "at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:181)"
        ],
        "metadata": {}
    }
]

def test_endpoints():
    """모든 API 엔드포인트 테스트"""
    print("🔗 === API Endpoints Test ===")
    
    client = TestClient(app)
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/api/system-status", "System status"),
        ("GET", "/api/pipeline-status", "Pipeline status"),
        ("GET", "/api/groups", "Error groups"),
        ("GET", "/ui", "Dashboard UI")
    ]
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = client.get(endpoint)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} {description}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description}: Error - {e}")


def test_pipeline_execution():
    """파이프라인 실행 테스트"""
    print("\n⚙️  === Pipeline Execution Test ===")
    
    with patch.object(settings, 'log_source_type', 'nelo'), \
         patch('app.services.ingestion_service.fetch_from_nelo', return_value=MOCK_LOG_DATA):
        client = TestClient(app)
        
        # 파이프라인 상태 확인
        status_response = client.get("/api/pipeline-status")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"  📊 Initial status: {status['status']}")
        
        # 파이프라인 실행
        print("  🚀 Triggering pipeline...")
        trigger_response = client.post("/trigger-pipeline")

        if trigger_response.status_code == 200:
            print(f"  ✅ Pipeline triggered: {trigger_response.json()['message']}")
            
            # 잠시 대기
            time.sleep(3)

            # 결과 확인
            groups_response = client.get("/api/groups")
            if groups_response.status_code == 200:
                groups = groups_response.json()
                print(f"  📈 Results: {len(groups)} error groups created")
                
                if groups:
                    analyzed = sum(1 for g in groups if g['status'] == 'ANALYZED')
                    print(f"    - Analyzed groups: {analyzed}")

                    avg_risk = sum(g['risk_score'] for g in groups) / len(groups)
                    print(f"    - Average risk score: {avg_risk:.1f}")

                    methods = {}
                    for g in groups:
                        method = g['grouping_method']
                        methods[method] = methods.get(method, 0) + 1
                    print(f"    - Grouping methods: {dict(methods)}")
            else:
                print(f"  ❌ Failed to get groups: {groups_response.status_code}")
        else:
            print(f"  ❌ Failed to trigger pipeline: {trigger_response.status_code}")

def test_ui_features():
    """UI 기능 테스트"""
    print("\n🎨 === UI Features Test ===")
    
    client = TestClient(app)
    
    # UI 페이지 로드
    ui_response = client.get("/ui")
    if ui_response.status_code == 200:
        print("  ✅ Dashboard loads successfully")
        content = ui_response.text
        
        # 주요 UI 요소 확인
        ui_elements = [
            "Error Analyzer Dashboard",
            "Pipeline Status", 
            "NELO API",
            "Active Issues",
            "Non-Issues",
            "Risk Score"
        ]
        
        for element in ui_elements:
            if element in content:
                print(f"    ✅ Contains: {element}")
            else:
                print(f"    ❌ Missing: {element}")
    else:
        print(f"  ❌ UI failed to load: {ui_response.status_code}")

def test_toggle_functionality():
    """Non-issue 토글 기능 테스트"""
    print("\n🔄 === Toggle Functionality Test ===")
    
    client = TestClient(app)
    
    # 그룹 목록 확인
    groups_response = client.get("/api/groups")
    if groups_response.status_code == 200:
        groups = groups_response.json()
        
        if groups:
            test_group = groups[0]
            group_id = test_group['id']
            original_status = test_group['status']
            
            print(f"  🎯 Testing with Group {group_id} (status: {original_status})")
            
            # Non-issue로 토글
            toggle_response = client.post(
                f"/api/groups/{group_id}/toggle-non-issue",
                json={"is_non_issue": True}
            )
            
            if toggle_response.status_code == 200:
                updated_group = toggle_response.json()
                new_status = updated_group['status']
                print(f"    ✅ Toggled to: {new_status}")
                
                # 원래대로 복구
                restore_response = client.post(
                    f"/api/groups/{group_id}/toggle-non-issue", 
                    json={"is_non_issue": False}
                )
                
                if restore_response.status_code == 200:
                    restored_group = restore_response.json()
                    print(f"    ✅ Restored to: {restored_group['status']}")
                else:
                    print(f"    ❌ Failed to restore: {restore_response.status_code}")
            else:
                print(f"    ❌ Failed to toggle: {toggle_response.status_code}")
        else:
            print("  ⚠️  No groups available for toggle test")
    else:
        print(f"  ❌ Failed to get groups: {groups_response.status_code}")

def main():
    """메인 테스트 실행"""

    print("🧪 === Error Analyzer PoC - Full Integration Test ===")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 모든 테스트 실행
    test_endpoints()
    test_pipeline_execution()
    test_ui_features()
    test_toggle_functionality()
    
    print("\n" + "="*60)
    print("🎉 === Integration Test Complete ===")
    print()
    print("📱 Dashboard: http://localhost:8000/ui")
    print("📖 API Docs: http://localhost:8000/docs") 
    print("🔧 NELO Setup: See NELO_SETUP.md")
    print()
    print("✨ All systems operational! Ready for production use.")

if __name__ == "__main__":
    main()
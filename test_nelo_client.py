#!/usr/bin/env python3
"""
NELO API 클라이언트 테스트 스크립트
실제 NELO API 연결을 테스트하고 디버깅합니다.
"""

import requests
import json
from datetime import datetime, timedelta
from app.config import settings
from app.services.nelo_client import NeloClient

def test_nelo_configuration():
    """NELO 설정 확인"""
    print("🔧 === NELO Configuration Check ===")
    print(f"NELO_API_URL: {settings.nelo_api_url}")
    print(f"NELO_GROUP_ID: {settings.nelo_group_id}")
    print(f"NELO_ACCESS_KEY: {settings.nelo_access_key}")
    print(f"NELO_SECRET_KEY: {'*' * len(settings.nelo_secret_key) if settings.nelo_secret_key else 'Not set'}")
    print(f"LOG_SOURCE_TYPE: {settings.log_source_type}")
    print()

def test_nelo_api_raw():
    """원본 NELO API 직접 호출 테스트"""
    print("🔗 === Raw NELO API Test ===")
    
    # 시간 범위 설정 (최근 1시간)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    from_time = int(start_time.timestamp() * 1000)
    to_time = int(end_time.timestamp() * 1000)
    
    headers = {
        "X-NELO-ACCESS-KEY-ID": settings.nelo_access_key,
        "X-NELO-SECRET-ACCESS-KEY": settings.nelo_secret_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "dataSource.groupId": settings.nelo_group_id,
        "query": "logLevel:ERROR",
        "fields": "logTime,logLevel,body,Location,clientIp,host,userId,projectName",
        "format": "json",
        "count": "10",
        "limit": "10",
        "compression": "false",
        "from": from_time,
        "to": to_time
    }
    
    print(f"Request URL: {settings.nelo_api_url}")
    print(f"Headers: X-NELO-ACCESS-KEY-ID={settings.nelo_access_key}")
    print(f"Time Range: {start_time} ~ {end_time}")
    print(f"Group ID: {settings.nelo_group_id}")
    print()
    
    try:
        print("📡 Sending request to NELO API...")
        response = requests.get(
            settings.nelo_api_url,
            headers=headers,
            params=params,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS: Received {len(data)} logs from NELO")
                
                if data:
                    print("\n📄 Sample log:")
                    print(json.dumps(data[0], indent=2, ensure_ascii=False))
                else:
                    print("⚠️  No logs found in the specified time range")
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text[:200]}")
                
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - API Key 문제")
            print("Response body:", response.text)
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden - 권한 문제")
            print("Response body:", response.text)
            
        elif response.status_code == 404:
            print("❌ 404 Not Found - Group ID 또는 URL 문제")
            print("Response body:", response.text)
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_nelo_client():
    """NeloClient 클래스 테스트"""
    print("\n🏗️  === NELO Client Class Test ===")
    
    client = NeloClient()
    
    print("Testing different time ranges...")
    
    # 다양한 시간 범위로 테스트
    time_ranges = [1, 5, 15, 60]  # 1분, 5분, 15분, 1시간
    
    for minutes in time_ranges:
        print(f"\n⏰ Testing {minutes} minutes back...")
        try:
            logs = client.fetch_error_logs(minutes_back=minutes)
            print(f"  Result: {len(logs)} logs fetched")
            
            if logs:
                sample_log = logs[0]
                print(f"  Sample keys: {list(sample_log.keys())}")
                print(f"  Sample project: {sample_log.get('projectName', 'N/A')}")
                break  # 로그를 찾으면 중단
                
        except Exception as e:
            print(f"  Error: {e}")

def test_different_queries():
    """다양한 쿼리로 테스트"""
    print("\n🔍 === Different Query Test ===")
    
    queries = [
        "logLevel:ERROR",
        "logLevel:WARN", 
        "*",  # 모든 로그
        "logLevel:ERROR OR logLevel:WARN",
        "body:exception",
        "body:error"
    ]
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=2)
    from_time = int(start_time.timestamp() * 1000)
    to_time = int(end_time.timestamp() * 1000)
    
    headers = {
        "X-NELO-ACCESS-KEY-ID": settings.nelo_access_key,
        "X-NELO-SECRET-ACCESS-KEY": settings.nelo_secret_key
    }
    
    for query in queries:
        print(f"\n🔎 Testing query: {query}")
        
        params = {
            "dataSource.groupId": settings.nelo_group_id,
            "query": query,
            "fields": "logTime,logLevel,body",
            "format": "json", 
            "count": "5",
            "compression": "false",
            "from": from_time,
            "to": to_time
        }
        
        try:
            response = requests.get(
                settings.nelo_api_url,
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ {len(data)} logs found")
                
                if data:
                    print(f"  Sample: {data[0].get('body', '')[:100]}...")
                    
            else:
                print(f"  ❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

def main():
    print("🧪 === NELO API Client Testing ===\n")
    
    # 1. 설정 확인
    test_nelo_configuration()
    
    # 2. 원본 API 테스트
    test_nelo_api_raw()
    
    # 3. 클라이언트 클래스 테스트
    test_nelo_client()
    
    # 4. 다양한 쿼리 테스트
    test_different_queries()
    
    print("\n" + "="*50)
    print("🎯 === Testing Summary ===")
    print("1. API 키가 유효하지 않으면 401 에러가 발생합니다")
    print("2. Group ID가 잘못되면 빈 결과나 403 에러가 발생합니다") 
    print("3. 시간 범위를 넓혀서 테스트해보세요")
    print("4. 다양한 쿼리를 시도해보세요")
    print("\n💡 Troubleshooting:")
    print("- NELO 웹 콘솔에서 API 키 재생성")
    print("- Group ID 확인")
    print("- 권한 설정 확인")
    print("- 네트워크 연결 상태 확인")

if __name__ == "__main__":
    main()
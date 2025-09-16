#!/usr/bin/env python3
"""
Azure 연결 상태 디버깅 스크립트
"""

import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# 환경 변수 로드
load_dotenv()

def check_env_variables():
    """환경 변수 확인"""
    print("=== 환경 변수 확인 ===")
    
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
        "AZURE_SEARCH_SERVICE_ENDPOINT": os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
        "AZURE_SEARCH_ADMIN_KEY": os.getenv("AZURE_SEARCH_ADMIN_KEY"),
        "AZURE_SEARCH_INDEX_NAME": os.getenv("AZURE_SEARCH_INDEX_NAME")
    }
    
    missing = []
    for key, value in required_vars.items():
        if value:
            print(f"✅ {key}: {value[:20]}..." if len(str(value)) > 20 else f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: 누락됨")
            missing.append(key)
    
    return len(missing) == 0

def test_azure_search():
    """Azure Search 연결 테스트"""
    print("\n=== Azure Search 연결 테스트 ===")
    
    try:
        search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
        )
        
        # 간단한 검색 테스트
        results = list(search_client.search("*", top=1))
        print(f"✅ Azure Search 연결 성공")
        print(f"📊 검색 결과: {len(results)}건")
        
        if results:
            print(f"📄 샘플 데이터: {results[0].get('error_code', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure Search 연결 실패: {str(e)}")
        return False

def test_azure_openai():
    """Azure OpenAI 연결 테스트"""
    print("\n=== Azure OpenAI 연결 테스트 ===")
    
    try:
        # 클라이언트 초기화
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        
        print(f"🔗 엔드포인트: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"📋 배포명: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        print(f"🔢 API 버전: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        
        # 간단한 테스트 호출
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        print("✅ Azure OpenAI 연결 성공")
        print(f"📝 응답: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI 연결 실패: {str(e)}")
        
        # 상세 오류 분석
        error_str = str(e)
        if "404" in error_str:
            print("\n🔍 404 오류 원인 분석:")
            print("1. 배포명(deployment name)이 올바른지 확인")
            print("2. Azure OpenAI 리소스에서 배포가 생성되었는지 확인")
            print("3. 엔드포인트 URL이 정확한지 확인")
        elif "401" in error_str:
            print("\n🔍 401 오류 원인 분석:")
            print("1. API 키가 올바른지 확인")
            print("2. API 키가 만료되지 않았는지 확인")
        elif "429" in error_str:
            print("\n🔍 429 오류 원인 분석:")
            print("1. 할당량(quota) 초과 확인")
            print("2. 요청 빈도 제한 확인")
        
        return False

def provide_solutions():
    """해결책 제공"""
    print("\n=== 일반적인 해결책 ===")
    print("""
🔧 Azure OpenAI 설정 확인사항:

1. Azure Portal에서 확인:
   - OpenAI 리소스 > 배포 > 배포명 확인
   - 올바른 모델(gpt-4o-mini 또는 gpt-4o)이 배포되어 있는지 확인
   - API 키 재생성 (Keys and Endpoint 메뉴)

2. .env 파일 수정:
   AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE-NAME.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=YOUR-ACTUAL-DEPLOYMENT-NAME
   AZURE_OPENAI_API_VERSION=2024-02-15-preview

3. 일반적인 배포명:
   - gpt-4o-mini
   - gpt-4o
   - gpt-35-turbo

4. 확인 방법:
   - Azure Portal > Azure OpenAI > 배포 탭에서 정확한 배포명 복사
   - 엔드포인트 URL에서 리소스명 확인
""")

def main():
    print("🔍 AIRA 시스템 연결 상태 진단")
    print("=" * 50)
    
    # 1. 환경 변수 확인
    if not check_env_variables():
        print("\n❌ 환경 변수 설정을 먼저 완료해주세요.")
        provide_solutions()
        return
    
    # 2. Azure Search 테스트
    search_ok = test_azure_search()
    
    # 3. Azure OpenAI 테스트
    openai_ok = test_azure_openai()
    
    # 4. 결과 요약
    print("\n=== 진단 결과 ===")
    print(f"Azure Search: {'✅ 정상' if search_ok else '❌ 오류'}")
    print(f"Azure OpenAI: {'✅ 정상' if openai_ok else '❌ 오류'}")
    
    if not openai_ok:
        provide_solutions()
    
    if search_ok and openai_ok:
        print("\n🎉 모든 연결이 정상입니다!")
        print("streamlit run app.py 로 시스템을 실행하세요.")

if __name__ == "__main__":
    main()
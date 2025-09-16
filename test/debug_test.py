import traceback
import sys

try:
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("✅ 임포트 성공")
    
    # 단계적 테스트
    print("1. 환경변수 확인...")
    endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "aira-errors-index")
    
    print(f"   Endpoint: {'있음' if endpoint else '없음'}")
    print(f"   API Key: {'있음' if api_key else '없음'}")
    print(f"   Index: {index_name}")
    
    print("2. Credential 생성...")
    credential = AzureKeyCredential(api_key)
    print("   ✅ Credential 생성 성공")
    
    print("3. SearchClient 생성...")
    client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=credential
    )
    print("   ✅ SearchClient 생성 성공")
    
    print("4. 검색 테스트...")
    results = client.search("*", top=1)
    list(results)  # 실제로 결과 가져오기
    print("   ✅ 검색 테스트 성공")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print(f"오류 타입: {type(e).__name__}")
    print("\n전체 스택 트레이스:")
    traceback.print_exc()
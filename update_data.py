import os
import json
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchableField
)
from azure.core.credentials import AzureKeyCredential

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("📁 .env 파일 로드됨")
except ImportError:
    print("ℹ️ python-dotenv가 설치되지 않음. 환경 변수를 직접 설정하세요.")

# Azure Search 설정
SEARCH_SERVICE_NAME = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
API_VERSION = "2023-11-01"

# Azure Search 엔드포인트
search_endpoint = f"{SEARCH_SERVICE_NAME}" if SEARCH_SERVICE_NAME else None

def check_environment():
    """환경 변수 확인"""
    if not SEARCH_SERVICE_NAME or not SEARCH_API_KEY:
        print("❌ Azure Search 환경 변수가 설정되지 않았습니다.")
        print("   필요한 환경 변수:")
        print("   - AZURE_SEARCH_SERVICE_NAME")
        print("   - AZURE_SEARCH_API_KEY")
        return False
    
    print(f"✅ Azure Search 서비스: {SEARCH_SERVICE_NAME}")
    print(f"✅ API 키: {'*' * (len(SEARCH_API_KEY) - 4) + SEARCH_API_KEY[-4:] if len(SEARCH_API_KEY) > 4 else '****'}")
    return True

def create_search_index():
    """Azure Search 인덱스 생성 - 기본 필드만 사용"""
    print("=== Azure Search 설정 시작 ===")
    
    credential = AzureKeyCredential(SEARCH_API_KEY)
    index_client = SearchIndexClient(
        endpoint=search_endpoint, 
        credential=credential,
        api_version=API_VERSION
    )
    
    try:
        # 기존 인덱스 삭제
        try:
            index_client.delete_index(INDEX_NAME)
            print(f"🗑️ 기존 인덱스 '{INDEX_NAME}' 삭제됨")
        except Exception:
            print(f"ℹ️ 기존 인덱스 '{INDEX_NAME}'가 없거나 삭제 실패")
        
        # 기본 필드만 사용한 인덱스 정의
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="error_code", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchableField(name="error_name", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchableField(name="symptoms", type=SearchFieldDataType.String),
            SearchableField(name="solution", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="severity", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="related_systems", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="monitoring_points", type=SearchFieldDataType.String),
            SearchableField(name="prevention", type=SearchFieldDataType.String),
            # occurred_at 필드 추가 (날짜/시간으로 저장)
            SimpleField(name="occurred_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SearchableField(name="system_status", type=SearchFieldDataType.String),
        ]
        
        # 인덱스 생성
        index = SearchIndex(name=INDEX_NAME, fields=fields)
        result = index_client.create_index(index)
        print(f"✅ 인덱스 '{INDEX_NAME}' 생성 완료")
        print(f"   필드 수: {len(fields)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")
        return False

def load_data():
    """JSON 데이터 파일 로드"""
    data_files = ['./data/error_data.json']
    
    for filename in data_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📄 데이터 파일 '{filename}' 로드 완료 ({len(data)}건)")
            return data
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"❌ '{filename}' 파일 읽기 오류: {e}")
            continue
    
    return None

def preprocess_data(data):
    """데이터 전처리 - 문제가 되는 필드 제거 및 정리"""
    processed_data = []
    fields_to_remove = ['system_resources']
    for i, item in enumerate(data.copy()):
        try:
            if 'id' not in item:
                item['id'] = str(i + 1)
            for field in fields_to_remove:
                if field in item:
                    del item[field]
            # occurred_at은 그대로 둠
            if 'system_status' in item and isinstance(item['system_status'], dict):
                item['system_status'] = json.dumps(item['system_status'], ensure_ascii=False)
            string_fields = ['error_code', 'error_name', 'description', 'symptoms', 'solution', 'category', 'severity']
            for field in string_fields:
                if field in item and item[field] is None:
                    item[field] = ""
            processed_data.append(item)
        except Exception as e:
            print(f"⚠️ 데이터 전처리 오류 (항목 {i}): {e}")
            continue
    print(f"🔄 데이터 전처리 완료: {len(processed_data)}/{len(data)}개 항목 처리됨")
    if fields_to_remove:
        print(f"   제거된 필드: {', '.join(fields_to_remove)}")
    return processed_data

def upload_data(data):
    """Azure Search에 데이터 업로드"""
    try:
        credential = AzureKeyCredential(SEARCH_API_KEY)
        search_client = SearchClient(
            endpoint=search_endpoint, 
            index_name=INDEX_NAME, 
            credential=credential,
            api_version=API_VERSION
        )
        
        # 데이터 전처리
        processed_data = preprocess_data(data)
        if not processed_data:
            print("❌ 처리할 데이터가 없습니다.")
            return False
        
        # 배치 업로드
        batch_size = 50
        total_uploaded = 0
        total_failed = 0
        
        print(f"📤 {len(processed_data)}개 문서를 {batch_size}개씩 배치 업로드 시작...")
        
        for i in range(0, len(processed_data), batch_size):
            batch = processed_data[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                print(f"   배치 {batch_num} 업로드 중... ({len(batch)}개 문서)")
                result = search_client.upload_documents(documents=batch)
                
                # 업로드 결과 확인
                successful_uploads = sum(1 for r in result if r.succeeded)
                failed_uploads = sum(1 for r in result if not r.succeeded)
                
                total_uploaded += successful_uploads
                total_failed += failed_uploads
                
                if failed_uploads > 0:
                    print(f"   ⚠️ 배치 {batch_num}: {successful_uploads}개 성공, {failed_uploads}개 실패")
                    for r in result:
                        if not r.succeeded:
                            print(f"      실패 문서 키: {r.key}, 오류: {r.error_message}")
                            break  # 첫 번째 오류만 출력
                else:
                    print(f"   ✅ 배치 {batch_num}: {successful_uploads}개 업로드 완료")
                    
            except Exception as batch_error:
                print(f"   ❌ 배치 {batch_num} 업로드 실패: {batch_error}")
                total_failed += len(batch)
                continue
        
        print(f"📊 업로드 완료: 성공 {total_uploaded}개, 실패 {total_failed}개")
        return total_uploaded > 0
        
    except Exception as e:
        print(f"❌ 데이터 업로드 오류: {e}")
        return False

def verify_upload():
    """업로드된 데이터 검증"""
    try:
        credential = AzureKeyCredential(SEARCH_API_KEY)
        search_client = SearchClient(
            endpoint=search_endpoint, 
            index_name=INDEX_NAME, 
            credential=credential,
            api_version=API_VERSION
        )
        
        # 간단한 검색으로 문서 수 확인
        results = search_client.search(search_text="*", include_total_count=True, top=1)
        total_count = results.get_count()
        
        print(f"🔍 업로드 검증: 인덱스에 {total_count}개 문서 존재")
        
        if total_count > 0:
            # 샘플 문서 1개 조회
            sample_results = search_client.search(search_text="*", top=1)
            for result in sample_results:
                print(f"📄 샘플 문서:")
                print(f"   ID: {result.get('id', 'N/A')}")
                print(f"   에러 코드: {result.get('error_code', 'N/A')}")
                print(f"   에러 이름: {result.get('error_name', 'N/A')}")
                print(f"   카테고리: {result.get('category', 'N/A')}")
                break
        
        return total_count > 0
        
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 Azure Search 데이터 업데이트 시작 (기본 스키마)")
    print("=" * 60)
    
    # 환경 변수 확인
    if not check_environment():
        return False
    
    # 1. 인덱스 생성
    if not create_search_index():
        return False
    
    # 2. 데이터 로드
    data = load_data()
    if not data:
        return False
    
    # 3. 데이터 업로드
    if not upload_data(data):
        return False
    
    # 4. 업로드 검증
    if not verify_upload():
        print("⚠️ 검증에 실패했지만 일부 데이터는 업로드되었을 수 있습니다.")
    
    print("=" * 60)
    print("🎉 Azure Search 데이터 업데이트 완료!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 모든 작업이 성공적으로 완료되었습니다.")
        else:
            print("\n❌ 작업 중 오류가 발생했습니다.")
            exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        exit(1)
    except Exception as e:
        print(f"\n💥 예상치 못한 오류 발생: {e}")
        exit(1)
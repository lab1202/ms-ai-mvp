import streamlit as st
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json
from datetime import datetime
import requests # slack webhook용

# 환경 변수 로드
load_dotenv()

# ===== Slack 알림 전송 함수 (최상단에 위치) =====
def send_to_slack(result, webhook_url):
    """검색 결과를 Slack으로 전송 (글자수 제한 없음)"""
    if not webhook_url.startswith("https://hooks.slack.com/services/") or "T" not in webhook_url or "B" not in webhook_url:
        return False, "❌ Slack Webhook URL이 올바르지 않습니다. Slack에서 발급받은 Webhook URL을 사용하세요."

    # 글자수 제한 없이 전체 메시지 전송
    message = {
        "text": f"🔎 검색 결과 알림\n\n{result}"
    }
    try:
        response = requests.post(webhook_url, json=message)
        # Slack은 200 OK와 'ok'라는 본문을 반환해야 정상
        if response.status_code == 200 and response.text.strip() == "ok":
            return True, "✅ Slack으로 전송 완료"
        else:
            return False, f"❌ Slack 전송 실패: {response.status_code} / 응답: {response.text}"
    except Exception as e:
        return False, f"❌ Slack 전송 중 예외 발생: {str(e)}"
# ===== 함수 끝 =====

# 페이지 설정
st.set_page_config(
    page_title="AIRA 이상징후 현황 조회 시스템",
    page_icon="📊",
    layout="wide"
)

# Azure OpenAI 클라이언트 초기화
@st.cache_resource
def init_openai_client():
    try:
        return AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        )
    except Exception as e:
        st.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
        return None

# Azure Search 클라이언트 초기화 (호환성 개선)
@st.cache_resource
def init_search_client():
    try:
        # 캐시 무효화를 위한 고유 키 생성
        import time
        cache_key = f"search_client_{int(time.time() // 300)}"  # 5분마다 갱신
        
        endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "aira-errors-index")
        api_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
        
        if not endpoint or not api_key:
            st.error("Azure Search 환경변수가 설정되지 않았습니다.")
            return None
        
        # 최소한의 파라미터로 클라이언트 생성
        credential = AzureKeyCredential(api_key)
        
        # 단계별 초기화로 오류 방지
        search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # 연결 테스트
        try:
            # 간단한 테스트 쿼리
            test_results = search_client.search("*", top=1)
            list(test_results)  # 결과를 실제로 가져와서 연결 확인
            return search_client
        except Exception as test_error:
            st.error(f"Azure Search 연결 테스트 실패: {str(test_error)}")
            return None
            
    except Exception as e:
        st.error(f"Search 클라이언트 초기화 실패: {str(e)}")
        return None

def get_system_status_summary(search_client):
    """전체 시스템 상태 요약 조회"""
    if not search_client:
        return {}, set()
        
    try:
        results = search_client.search(
            search_text="*",
            top=50,
            select="system_status,related_systems"
        )
        
        system_status_count = {}
        all_systems = set()
        
        for result in results:
            if result.get('system_status'):
                try:
                    status_dict = json.loads(result['system_status'])
                    for system, status in status_dict.items():
                        all_systems.add(system)
                        if status not in system_status_count:
                            system_status_count[status] = set()
                        system_status_count[status].add(system)
                except:
                    continue
        
        return system_status_count, all_systems
    except Exception as e:
        st.error(f"시스템 상태 조회 오류: {str(e)}")
        return {}, set()

def search_errors(query, search_client):
    """Azure Search를 사용하여 에러 검색"""
    if not search_client:
        return []
        
    try:
        results = search_client.search(
            search_text=query,
            top=3,
            include_total_count=True
        )
        return list(results)
    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []

def generate_response(query, search_results, openai_client):
    """OpenAI를 사용하여 응답 생성"""
    
    if not openai_client:
        return "OpenAI 클라이언트가 초기화되지 않았습니다."
    
    # 검색 결과를 컨텍스트로 구성
    context = ""
    if search_results:
        context = "\n\n관련 에러 정보:\n"
        for result in search_results:
            # system_status JSON 파싱
            system_status_str = ""
            if result.get('system_status'):
                try:
                    system_status = json.loads(result['system_status'])
                    system_status_str = f"\n시스템 상태: {', '.join([f'{k}({v})' for k, v in system_status.items()])}"
                except:
                    pass
            
            context += f"""
에러 코드: {result.get('error_code', 'N/A')}
에러명: {result.get('error_name', 'N/A')} 
설명: {result.get('description', 'N/A')}
증상: {result.get('symptoms', 'N/A')}
해결 방법: {result.get('solution', 'N/A')}
카테고리: {result.get('category', 'N/A')}
심각도: {result.get('severity', 'N/A')}
관련 시스템: {result.get('related_systems', 'N/A')}{system_status_str}
---
"""

    system_prompt = f"""당신은 AIRA 이상징후 현황 조회 시스템의 AI 어시스턴트입니다.
MSA 환경에서 핸드폰 개통(신규개통, 번호이동, 기기변경) 시 발생하는 에러들에 대해 전문적으로 답변합니다.

사용자의 질문에 대해 다음과 같이 답변해주세요:
1. 문제 상황 분석
2. 가능한 원인 설명  
3. 단계별 해결 방법 제시
4. 관련 시스템 상태 안내
5. 예방 조치 안내

답변은 친근하고 이해하기 쉽게 작성해주세요.
{context}
"""

    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"

def render_system_status_sidebar(search_client):
    """사이드바에 시스템 상태 표시"""
    with st.sidebar:
        st.header("🖥️ 시스템 상태")
        
        # # 상태 갱신 버튼
        # if st.button("🔄 상태 갱신", key="refresh_status"):
        #     st.cache_resource.clear()
        
        if not search_client:
            st.error("Search 클라이언트가 초기화되지 않았습니다.")
            return
        
        # 시스템 상태 조회
        system_status_count, all_systems = get_system_status_summary(search_client)
        
        if system_status_count:
            # 전체 상태 요약
            total_systems = len(all_systems)
            normal_systems = len(system_status_count.get('정상', set()))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("전체 시스템", total_systems)
            with col2:
                st.metric("정상 시스템", normal_systems)
            
            # 상태별 세부 정보
            st.markdown("### 📊 상태별 현황")
            
            status_colors = {
                '정상': '🟢',
                '지연': '🟡', 
                '일부지연': '🟡',
                '일시적오류': '🟠',
                '높은부하': '🟠',
                '점검중': '🔴'
            }
            
            for status, systems in system_status_count.items():
                if systems:
                    color = status_colors.get(status, '⚪')
                    with st.expander(f"{color} {status} ({len(systems)}개)"):
                        for system in sorted(systems):
                            st.write(f"• {system}")
            
            # 마지막 업데이트 시간
            st.caption(f"⏰ 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("시스템 상태 정보를 불러올 수 없습니다.")

def main():
    # 헤더
    st.title("AIRA AI Assistant")
    st.markdown("스마트폰 개통 에러 진단 및 원인분석 지원 서비스")
    
    # 클라이언트 초기화
    # st.write("🔄 시스템 초기화 중...")
    
    try:
        openai_client = init_openai_client()
        search_client = init_search_client()
        
        if not openai_client or not search_client:
            st.error("시스템 초기화에 실패했습니다. 환경변수를 확인해주세요.")
            st.info("""
            **필요한 환경변수:**
            - AZURE_SEARCH_SERVICE_ENDPOINT
            - AZURE_SEARCH_INDEX_NAME  
            - AZURE_SEARCH_ADMIN_KEY
            - AZURE_OPENAI_ENDPOINT
            - AZURE_OPENAI_API_KEY
            - AZURE_OPENAI_API_VERSION
            - AZURE_OPENAI_DEPLOYMENT_NAME
            """)
            st.stop()
        
        st.success("✅ 시스템이 성공적으로 초기화되었습니다!")
        
    except Exception as e:
        st.error(f"시스템 초기화 오류: {str(e)}")
        st.stop()
    
    # 사이드바 - 시스템 상태
    render_system_status_sidebar(search_client)
    
    # 사이드바 - 기본 정보
    # with st.sidebar:
    #     st.markdown("---")
    #     st.header("📋 시스템 정보")
    #     st.info("📱 신규개통\n📞 번호이동\n🔄 기기변경")
        
    #     st.header("🏷️ 에러 카테고리")
    #     categories = ["전체", "신규개통", "번호이동", "기기변경"]
    #     selected_category = st.selectbox("카테고리 선택", categories)
        
    #     st.header("⚠️ 심각도")
    #     severities = ["전체", "높음", "중간", "낮음"]
    #     selected_severity = st.selectbox("심각도 선택", severities)
    
    # 채팅 인터페이스
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "안녕하세요! AIRA 시스템입니다. \n\nMSA 환경에서 핸드폰 개통 시 발생하는 문제점이나 에러에 대해 질문해주세요.\n\n**예시 질문:**\n- '신규개통 시 본인인증이 안 돼요'\n- 'MSA-001 에러가 발생했어요'\n- '번호이동 중에 오류가 생겼어요'\n- '시스템 상태는 어떤가요?'"
        })

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력
    if prompt := st.chat_input("에러나 문제 상황을 입력해주세요"):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 검색 및 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                search_results = search_errors(prompt, search_client)
                response = generate_response(prompt, search_results, openai_client)
                st.markdown(response)
                
                # 관련 에러 정보 표시
                if search_results:
                    st.markdown("---")
                    st.markdown("### 📋 관련 에러 정보")
                    for i, result in enumerate(search_results, 1):
                        with st.expander(f"📸 {result.get('error_code', 'N/A')} - {result.get('error_name', 'N/A')}"):
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.markdown(f"**카테고리:** {result.get('category', 'N/A')}")
                                st.markdown(f"**심각도:** {result.get('severity', 'N/A')}")
                                st.markdown(f"**증상:** {result.get('symptoms', 'N/A')}")
                            
                            with col2:
                                st.markdown(f"**관련 시스템:** {result.get('related_systems', 'N/A')}")
                                
                                # 시스템 상태 표시
                                if result.get('system_status'):
                                    try:
                                        system_status = json.loads(result['system_status'])
                                        st.markdown("**시스템 상태:**")
                                        for system, status in system_status.items():
                                            status_icon = "🟢" if status == "정상" else "🟡" if "지연" in status else "🟠" if "오류" in status or "부하" in status else "🔴"
                                            st.markdown(f"  {status_icon} {system}: {status}")
                                    except:
                                        pass
                            
                            st.markdown(f"**해결방법:** {result.get('solution', 'N/A')}")
                            
                            if result.get('prevention'):
                                st.markdown(f"**예방조치:** {result.get('prevention', 'N/A')}")
        
        # 어시스턴트 응답 저장
        st.session_state.messages.append({"role": "assistant", "content": response})

    # 하단 버튼
    slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    btn1, btn2, btn3, _ = st.columns([2, 2, 2, 0.5])

    with btn1:
        if st.button("🆂 Slack으로 결과 전송", key="send_to_slack_btn_main"):
            assistant_messages = [m for m in st.session_state.messages if m["role"] == "assistant"]
            if not slack_webhook_url:
                st.error("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
            elif not assistant_messages:
                st.error("전송할 assistant 응답이 없습니다.")
            else:
                latest_response = assistant_messages[-1]["content"]
                ok, msg = send_to_slack(latest_response, slack_webhook_url)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.code(latest_response, language="markdown")
                    st.code(slack_webhook_url, language="text")

    with btn2:
        if st.button("💬 채팅 초기화", key="reset_chat_btn"):
            st.session_state.messages = []
            st.rerun()

    with btn3:
        if st.button("ℹ️ 도움말", key="help_btn"):
            st.info("**사용법:**\n1. 에러 코드나 증상을 입력하세요\n2. AI가 관련 정보를 검색하여 해결책을 제공합니다\n3. 사이드바에서 실시간 시스템 상태를 확인하세요")

if __name__ == "__main__":
    main()

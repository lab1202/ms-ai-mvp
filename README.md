# 🔍 AIRA 이상징후 현황 조회 시스템

접속 URL : ktds505.azurewebsites.net

MSA 환경에서 모바일 개통 시 발생하는 에러들을 분석하고 해결 방법을 제공하는 AI 기반 지원 시스템입니다.

## 📋 주요 기능

- **실시간 에러 검색**: Azure Search를 통한 빠른 에러 정보 검색
- **AI 기반 해결책 제공**: Azure OpenAI를 활용한 맞춤형 해결 방법 제안
- **시스템 상태 모니터링**: 실시간 관련 시스템 상태 확인 (NEW!)
- **다양한 개통 유형 지원**: 신규개통, 번호이동, 기기변경 에러 커버
- **직관적인 채팅 인터페이스**: Streamlit 기반의 사용자 친화적 UI

## 🛠️ 시스템 구성

```
aira-system/
├── app.py                 # 메인 애플리케이션 (시스템 상태 모니터링 추가)
├── update_data.py         # 데이터 업데이트 스크립트
├── requirements.txt       # Python 패키지 의존성
├── .env                   # 환경 변수 템플릿
├── .gitignore             # Git 제외 파일 목록
├── data/
│   └── error_data.json   # MSA 핸드폰 개통 에러 데이터 (30건, 시스템 상태 포함)
└── README.md            # 프로젝트 설명
```

## ⚙️ 설치 및 설정

### 1. Python 환경 확인
- Python 3.13+ 권장
- pip 패키지 매니저 필요

### 2. 프로젝트 설정

```bash
# 저장소 클론 또는 파일 다운로드
git clone <repository-url>
cd ms-ai-mvp

# 새 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 환경 변수 파일 생성
cp .env.example .env
# .env 파일을 열어서 Azure 리소스 정보 입력
```bash
# Azure OpenAI 설정
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_API_VERSION=

# Azure Search 설정
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key-here
AZURE_SEARCH_INDEX_NAME=
```

## 🚀 시스템 실행

```bash
./streamlit.sh  # 의존성 생성 및 실행
# 또는
streamlit run app.py
```

브라우저에서 `http://localhost:8000`으로 접속하여 시스템을 사용할 수 있습니다.

## 🔄 데이터 업데이트

새로운 에러 데이터로 업데이트하려면:

```bash
python update_data.py
```

## 💡 사용 방법

1. **에러 문의**: 채팅창에 발생한 문제나 에러 코드를 입력
2. **AI 분석**: 시스템이 자동으로 관련 정보를 검색하고 해결책 제공
3. **시스템 상태 확인**: 왼쪽 사이드바에서 실시간 시스템 상태 모니터링
4. **상세 정보**: 관련된 에러 정보와 단계별 해결 방법 확인

### 예시 질문
- "신규개통 시 본인인증이 안 돼요"
- "MSA-001 에러가 발생했어요"
- "번호이동 중에 오류가 생겼어요"
- "기기변경 후 네트워크 연결이 안돼요"
- "시스템 상태는 어떤가요?"

## 📊 지원 에러 유형 (30건)

### 신규개통 (15건)
- 고객정보 검증 실패 (MSA-001)
- 신용정보 조회 실패 (MSA-009) 
- 중복 가입 방지 오류 (MSA-010)
- 통신비 미납 이력 확인 (MSA-011)
- 가족 관계 확인 실패 (MSA-012)
- 외국인 등록번호 검증 실패 (MSA-013)
- 법인 사업자번호 검증 오류 (MSA-014)
- 미성년자 법정대리인 동의 오류 (MSA-015)
- 요금제 적용 오류 (MSA-004)
- 결제수단 검증 실패 (MSA-006)
- 재고 부족 오류 (MSA-007)
- 네트워크 연동 타임아웃 (MSA-008)
- 서비스 활성화 지연 (MSA-029)
- 고객정보 동기화 실패 (MSA-030)

### 번호이동 (8건)
- 번호 포팅 조회 실패 (MSA-002)
- 포팅 승인번호 만료 (MSA-016)
- 포팅 대상 번호 오류 (MSA-017)
- 포팅 명의자 불일치 (MSA-018)
- 포팅 제한 번호 (MSA-019)
- 기존 통신사 해지 미완료 (MSA-020)
- 동시 포팅 신청 오류 (MSA-021)
- 포팅 수수료 결제 실패 (MSA-022)

### 기기변경 (7건)
- USIM 활성화 실패 (MSA-003)
- 기기 호환성 검증 실패 (MSA-005)
- USIM 카드 불량 (MSA-023)
- 기기 IMEI 등록 실패 (MSA-024)
- 기기 잠금 해제 실패 (MSA-025)
- 기기 소프트웨어 호환성 오류 (MSA-026)
- 데이터 백업 복원 실패 (MSA-027)
- 기기 보안 설정 충돌 (MSA-028)

## 🖥️ 시스템 상태 모니터링 (NEW!)

### 실시간 상태 확인
- **전체 시스템 개수**: 연관된 모든 시스템 수
- **정상 시스템 개수**: 정상 작동 중인 시스템 수
- **상태별 분류**: 정상/지연/오류/부하/점검 상태별 시스템 목록

### 상태 표시 아이콘
- 🟢 정상: 시스템이 정상 작동 중
- 🟡 지연: 응답 시간 지연 발생
- 🟠 오류/부하: 일시적 오류나 높은 부하 상태
- 🔴 점검중: 시스템 점검 또는 서비스 중단

### 모니터링 대상 시스템
- **인증 관련**: 본인인증API, 신용조회시스템, 외국인등록시스템
- **포팅 관련**: 포팅센터API, 통신사포팅서버, 승인관리시스템
- **결제 관련**: 결제게이트웨이, 금융기관API, 카드사시스템
- **네트워크**: HLR서버, 네트워크인증서버, 로드밸런서
- **관리 시스템**: 고객정보DB, 재고관리시스템, 과금시스템

## 🔧 트러블슈팅

### 일반적인 문제 해결

1. **Azure Search 연결 오류**
   ```bash
   # Azure Search 서비스 상태 확인
   # .env 파일의 AZURE_SEARCH_* 설정 재확인
   python setup_search.py
   ```

2. **OpenAI API 오류**
   ```bash
   # API 키와 엔드포인트 확인
   # 배포 모델명 확인 (gpt-4o-mini)
   ```

3. **데이터 업로드 실패**
   ```bash
   # data/error_data.json 파일 존재 확인
   # JSON 형식 유효성 검증
   python -m json.tool data/error_data.json
   ```

4. **시스템 상태 표시 안됨**
   ```bash
   # 사이드바에서 "상태 갱신" 버튼 클릭
   # 또는 "데이터 갱신" 버튼 클릭
   ```

### 로그 확인
- Streamlit 콘솔에서 에러 메시지 확인
- Azure Portal에서 Search Service 로그 확인

## 📈 시스템 확장

### 새로운 에러 유형 추가
1. `data/error_data.json`에 새 에러 정보 추가 (시스템 상태 정보 포함)
2. `python update_data.py` 실행하여# 🔍 AIRA 이상징후 현황 조회 시스템

## 🏗️ 아키텍처

```
[사용자] ↔ [Streamlit UI] ↔ [검색 로직] ↔ [Azure Search]
                ↓
         [OpenAI GPT-4o-mini] ← [컨텍스트 구성]
```

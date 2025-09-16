#!/bin/bash

# AIRA 이상징후 현황 조회 시스템 설정 스크립트

echo "=== AIRA 시스템 설정 시작 ==="

# 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. .env.example을 참조하여 .env 파일을 생성해주세요."
    exit 1
fi

# 필요한 패키지 설치
echo "📦 Python 패키지 설치 중..."
pip install streamlit \
    python-dotenv \
    openai \
    azure-search-documents==11.3.0 \
    azure-core==1.26.4

# Azure Search 인덱스 생성 및 데이터 업로드
echo "🔍 Azure Search 설정 중..."
python update_data.py

echo "✅ 설정이 완료되었습니다!"
python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0


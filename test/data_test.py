import json

try:
    with open('error_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ JSON 파일이 유효합니다. {len(data)}개 레코드 발견")
    
    # 다시 저장해서 포맷팅 정리
    with open('error_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ JSON 파일이 재포맷되었습니다.")
        
except json.JSONDecodeError as e:
    print(f"❌ JSON 오류: {e}")
    print(f"오류 위치: 줄 {e.lineno}, 열 {e.colno}")
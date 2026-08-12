import json
import os
import re

# 1. 처리할 원본 JSON 파일 이름 지정
input_filename = 'hsk-words-1.json'

# 원본 파일명에서 확장자를 제외한 이름 추출 후 '-cleaned.json' 붙이기 (예: 'hsk-words-1-cleaned.json')
base_name = os.path.splitext(input_filename)[0]
output_filename = f"{base_name}-cleaned.json"

# 브라우저로 수집한 원본 JSON 파일 읽기
with open(input_filename, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

all_words = []

for page_item in raw_data:
    text_content = page_item.get('text', '')
    lines = text_content.split('\n')
    
    for line in lines:
        parts = line.split('\t')
        
        if len(parts) >= 4:
            word = parts[0].strip()
            pinyin = parts[1].strip()
            
            if len(parts) >= 5 and parts[2].strip():
                part_of_speech = parts[2].strip()
                translation = parts[3].strip()
            else:
                part_of_speech = ""
                translation = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else parts[3].strip()

            if word and word not in ["Words", "Search", "View Test Dates", "TOP"]:
                if not any(d['word'] == word for d in all_words):
                    all_words.append({
                        "word": word,
                        "pinyin": pinyin,
                        "part of speech": part_of_speech,
                        "translation": translation
                    })

# 2. 동적으로 생성된 파일명으로 저장
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(all_words, f, ensure_ascii=False, indent=2)

print(f"변환 완료! 총 {len(all_words)}개의 단어가 '{output_filename}' 파일로 저장되었습니다.")
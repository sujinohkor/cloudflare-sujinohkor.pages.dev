import json
import os
import re

# 1. 처리할 HSK 레벨별 원본 파일 매핑 (7~9급은 '79' 키 사용)
file_mappings = {
    '1': 'hsk-words-1.json',
    '2': 'hsk-words-2.json',
    '3': 'hsk-words-3.json',
    '4': 'hsk-words-4.json',
    '5': 'hsk-words-5.json',
    '6': 'hsk-words-6.json',
    '79': 'hsk-words-79.json'
}

combined_dict = {}

# 2. 각 파일을 순회하며 파싱 및 통합
for level_key, input_filename in file_mappings.items():
    level = int(level_key) if level_key != '79' else 7
    
    if not os.path.exists(input_filename):
        print(f"경고: '{input_filename}' 파일이 존재하지 않아 건너뜁니다.")
        continue

    # 원본 JSON 파일 읽기
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

    # 추출된 단어들을 최종 딕셔너리에 레벨 정보와 함께 병합
    for entry in all_words:
        word = entry.get("word")
        if word:
            combined_dict[word] = {
                "level": level,
                "pinyin": entry.get("pinyin"),
                "part of speech": entry.get("part of speech"),
                "translation": entry.get("translation")
            }
    
    print(f"'{input_filename}' 처리 완료 (레벨 {level})")

# 3. 최종 통합된 딕셔너리를 하나의 JSON 파일로 저장
output_path = 'hsk-combined-words.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(combined_dict, f, ensure_ascii=False, indent=2)

print(f"\n모든 작업 완료! 총 {len(combined_dict)}개의 단어가 '{output_path}' 파일로 통합 저장되었습니다.")
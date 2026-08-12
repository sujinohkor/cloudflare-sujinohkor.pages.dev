import json
import os

# 파일 경로 매핑
file_mappings = {
    '1': 'hsk-words-1-cleaned.json',
    '2': 'hsk-words-2-cleaned.json',
    '3': 'hsk-words-3-cleaned.json',
    '4': 'hsk-words-4-cleaned.json',
    '5': 'hsk-words-5-cleaned.json',
    '6': 'hsk-words-6-cleaned.json',
    '79': 'hsk-words-79-cleaned.json'
}

combined_dict = {}

# 각 파일을 순회하며 통합
for level_key, file_path in file_mappings.items():
    level = int(level_key) if level_key != '79' else 7
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                word = entry.get("word")
                if word:
                    combined_dict[word] = {
                        "level": level,
                        "pinyin": entry.get("pinyin"),
                        "part of speech": entry.get("part of speech"),
                        "translation": entry.get("translation")
                    }

# 통합된 파일 저장
output_path = 'hsk-combined-words.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(combined_dict, f, ensure_ascii=False, indent=2)

print(f"통합 완료: {output_path}")
import pandas as pd
import json

def excel_to_custom_json(excel_path, json_path):
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_path)
    
    data_dict = {}
    
    # 각 행을 순회하며 JSON 구조 생성
    for _, row in df.iterrows():
        word = str(row['word'])
        data_dict[word] = {
            "level": str(row['level']),
            "pinyin": str(row['pinyin']),
            "part of speech": str(row['part of speech']),
            "translation": str(row['translation']),
            "translation(ko)": str(row['translation(ko)'])
        }
    
    # JSON 파일 저장
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)

# 실행
excel_to_custom_json('hsk-with-ko-words.xlsx', 'hsk-combined-words.json')
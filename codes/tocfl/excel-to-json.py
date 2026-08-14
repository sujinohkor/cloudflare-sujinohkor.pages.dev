import pandas as pd
import json
import re

excel_path = "8000zhuyin-translate(en,ko).xlsx" 
xls = pd.ExcelFile(excel_path)

target_sheets = [
    '準備級一級(Novice 1)', '準備級二級(Novice 2)', 
    '入門級(Level 1)', '基礎級(Level 2)', 
    '進階級(Level 3)', '高階級(Level 4)', '流利級(Level 5)'
]

result_data = {}

for sheet_name in target_sheets:
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    vocab_col = [c for c in df.columns if 'Vocabulary' in c][0]
    pinyin_col = [c for c in df.columns if 'Pinyin' in c][0]
    pos_col = [c for c in df.columns if 'Parts of Speech' in c][0]
    
    for idx, row in df.iterrows():
        vocab_raw = str(row[vocab_col]).strip() if pd.notna(row[vocab_col]) else ""
        if not vocab_raw or vocab_raw == "nan": 
            continue
            
        pinyin = str(row[pinyin_col]).strip() if pd.notna(row[pinyin_col]) else ""
        pos = str(row[pos_col]).strip() if pd.notna(row[pos_col]) else ""
        
        # 정확한 인덱스 지정: D열(Meaning (EN)) = 인덱스 3, E열(Meaning (KO)) = 인덱스 4
        eng_trans = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
        ko_trans = str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else ""
        
        # 괄호 제거 로직: translation 및 translation(ko)의 모든 괄호 제거
        eng_trans = re.sub(r'[()]', '', eng_trans)
        ko_trans = re.sub(r'[()]', '', ko_trans)
        
        # 세미콜론 앞 공백만 제거 (뒤 공백은 유지)
        eng_trans = re.sub(r'\s+;', ';', eng_trans)
        
        # 'nan' 문자열 처리
        if pinyin == "nan": pinyin = ""
        if pos == "nan": pos = ""
        if eng_trans == "nan": eng_trans = ""
        if ko_trans == "nan": ko_trans = ""
        
        item_data = {
            "level": sheet_name,
            "pinyin": pinyin,
            "part of speech": pos,
            "translation": eng_trans,     # D열 (Meaning (EN))
            "translation(ko)": ko_trans    # E열 (Meaning (KO))
        }
        
        # 슬래시('/') 또는 콤마 등으로 분리될 수 있는 기본 처리 후, 단어별 파싱 수행
        sub_keys = vocab_raw.split('/')
        for sub_key in sub_keys:
            clean_sub = sub_key.strip()
            if not clean_sub:
                continue
                
            # 괄호 패턴 분석
            match = re.search(r'^(.*?)\((.*?)\)(.*)$', clean_sub)
            if match:
                prefix, inner, suffix = match.groups()
                full_base = prefix + inner + suffix
                
                # 괄호 안의 내용이 한자(CJK Unified Ideographs)를 포함하는지 확인
                has_hanzi = bool(re.search(r'[\u4e00-\u9fff]', inner))
                
                if has_hanzi:
                    # 예: 電視(機) -> '電視', '電視機' 둘 다 저장
                    key_without_paren = prefix + suffix
                    result_data[key_without_paren] = item_data.copy()
                    result_data[full_base] = item_data.copy()
                else:
                    # 예: 沒關係(˙ㄒㄧ) -> '沒關係'만 저장
                    key_without_paren = prefix + suffix
                    result_data[key_without_paren] = item_data.copy()
            else:
                result_data[clean_sub] = item_data.copy()

# 최종 JSON 파일로 저장
output_filename = "tocfl-combined-words.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"JSON 파일 생성 완료! ({output_filename})")
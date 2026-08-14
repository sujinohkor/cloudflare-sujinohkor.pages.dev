import pandas as pd
import json

def convert_json_to_excel(input_filename, output_filename):
    # JSON 파일 읽기
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"오류: '{input_filename}' 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print(f"오류: '{input_filename}' 파일 형식이 올바른 JSON이 아닙니다.")
        return

    # 데이터 구조 변환 (딕셔너리 구조가 기존 예시와 같다고 가정)
    data_list = []
    for word, info in data.items():
        record = info.copy()
        record['word'] = word
        data_list.append(record)

    # DataFrame 생성
    df = pd.DataFrame(data_list)
    
    # 컬럼 순서 조정 (JSON 키가 데이터와 일치해야 함)
    # 기존 예시의 키: level, pinyin, part of speech, translation
    cols = ['word', 'level', 'pinyin', 'part of speech', 'translation']
    
    # 데이터프레임에 존재하는 컬럼만 선택
    existing_cols = [c for c in cols if c in df.columns]
    df = df[existing_cols]

    # 엑셀 파일로 저장
    df.to_excel(output_filename, index=False)
    print(f"변환 완료: {output_filename}")

# 함수 실행
if __name__ == "__main__":
    convert_json_to_excel('hsk-without-ko-words.json', 'hsk-without-ko-words.xlsx')
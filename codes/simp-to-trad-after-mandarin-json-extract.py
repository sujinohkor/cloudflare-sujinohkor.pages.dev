import re
import opencc

# 간체에서 번체로 변환하는 객체 생성
converter = opencc.OpenCC("s2t")

# 1. 파일 읽기
with open('manda.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 진행 상황 출력을 위한 카운터
count = [0]

# 2. 정규식을 이용해 char: '글자' 패턴만 찾아내어 번체로 치환
def replace_char(match):
    prefix = match.group(1)      # char: '
    char_val = match.group(2)    # 간체자 글자
    suffix = match.group(3)      # '
    
    count[0] += 1
    # 실시간으로 몇 번째 글자를 변환 중인지 출력 (\r을 사용하여 줄 바꿈 없이 갱신)
    print(f"\r진행 중: {count[0]}번째 글자 변환 중 ('{char_val}' -> '{converter.convert(char_val)}')", end="", flush=True)
    
    # 해당 글자만 번체로 변환
    converted_char = converter.convert(char_val)
    return f"{prefix}{converted_char}{suffix}"

print("변환을 시작합니다...")
pattern = re.compile(r"(char\s*:\s*['\"])([^'\"]+)(['\"])")
traditional_content = pattern.sub(replace_char, content)

print("\n") # 줄바꿈

# 3. 결과 파일로 저장
with open('trad_with_simp.txt', 'w', encoding='utf-8') as f:
    f.write(traditional_content)

print(f"변환 완료! 총 {count[0]}개의 글자가 번체로 변환되었습니다.")
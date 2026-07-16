import re
import os

def parse_colors():
    input_file = "color-namer.min.js"
    output_file = "result.txt"
    
    # 1. 파일 존재 여부 확인
    if not os.path.exists(input_file):
        print(f"오류: '{input_file}' 파일을 찾을 수 없습니다.")
        print(f"실행 위치: {os.getcwd()} 폴더에 파일이 있는지 확인하세요.")
        return

    # 2. 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. 정규표현식으로 name과 hex 추출
    # {name:"...",hex:"#..."} 패턴을 검색
    pattern = re.compile(r'name\s*:\s*["\']([^"\']+)["\']\s*,\s*hex\s*:\s*["\']#?([0-9a-fA-F]+)["\']')
    matches = pattern.findall(content)
    
    print(f"데이터 추출 중... 총 {len(matches)}개의 색상을 발견했습니다.")
    
    if len(matches) == 0:
        print("데이터를 찾지 못했습니다. 파일 내용이 예상과 다를 수 있습니다.")
        return

    # 4. 결과 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("const ntcColors = [\n")
        # 리스트 컴프리헨션을 사용하여 깔끔하게 포맷팅
        formatted_lines = [f'    ["{h.upper()}", "{n.lower()}"]' for n, h in matches]
        f.write(",\n".join(formatted_lines))
        f.write("\n];")
        
    print(f"완료! '{output_file}' 파일이 생성되었습니다.")

if __name__ == "__main__":
    parse_colors()


#CMD에서 실행하는 방법
#터미널이나 CMD를 열고 다음과 같이 파일명을 입력하여 실행하시면 됩니다.
# 1. 기본 출력(result.txt로 저장):
# Bash
# python parse.py 내데이터.txt
#
# 2. 출력 파일명을 직접 지정할 때:
# Bash
# python parse.py 내데이터.txt 내결과물.txt
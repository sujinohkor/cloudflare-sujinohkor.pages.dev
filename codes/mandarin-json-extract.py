import html.parser
import urllib.request
import urllib.error

# HTML 파싱 클래스
class HanziParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.current_cell_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif self.in_table and tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif self.in_row and (tag == 'td' or tag == 'th'):
            self.in_cell = True
            self.current_cell_data = []

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif self.in_table and tag == 'tr':
            if self.in_row and len(self.current_row) >= 5:
                self.results.append(self.current_row)
            self.in_row = False
        elif self.in_row and (tag == 'td' or tag == 'th'):
            self.in_cell = False
            cell_text = "".join(self.current_cell_data).strip()
            self.current_row.append(cell_text)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_data.append(data)

results = []

# 1페이지부터 100페이지까지 순회 (전체를 원하시면 range(1, 101)로 변경하세요)
for page in range(1, 101):
    url = f'http://hanzidb.org/character-list/by-frequency?page={page}'
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            
            parser = HanziParser()
            parser.feed(html_content)
            
            # 첫 번째 행(헤더) 제외하고 데이터 추출
            for cols in parser.results[1:]:
                if len(cols) >= 5:
                    char = cols[0]
                    pinyin = cols[1]
                    definition = cols[2]
                    radical = cols[3].split()[0] if cols[3] else ''
                    strokes = cols[4]
                    
                    chinese = f"{char} ({pinyin})" if pinyin else char
                    strokes_int = int(strokes) if strokes.isdigit() else 0
                    
                    # 요청하신 JS 배열 객체 포맷으로 구성
                    # (meaning은 웹사이트의 영문 뜻을 그대로 넣거나 필요시 매핑 가능)
                    line = f"            {{ char: '{char}', meaning: '{definition}', chinese: '{chinese}', busu: '{radical}', strokes: {strokes_int} }},"
                    results.append(line)
                    
        print(f'{page}페이지 완료 (누적: {len(results)}개)')
    except Exception as e:
        print(f'페이지 {page} 로드 실패: {e}')

# TXT 파일로 자바스크립트 배열 형식 감싸서 저장
with open('characters.txt', 'w', encoding='utf-8') as f:
    f.write("const manda = [\n")
    for item in results:
        f.write(item + '\n')
    f.write("];\n")

print('TXT 파일 저장 완료! (const db 형식)')
chunk_size = 20 * 1024 * 1024     # 20MB 단위로 쪼개기 (안전하게 20MB 미만으로 설정)
file_name = 'mandarin.onnx'       # 본인의 ONNX 파일 이름으로 변경

with open(file_name, 'rb') as f:
    chunk_num = 1
    while True:
        chunk_data = f.read(chunk_size)
        if not chunk_data:
            break
        with open(f"{file_name}.part{chunk_num}", 'wb') as chunk_file:
            chunk_file.write(chunk_data)
        print(f"Part {chunk_num} 생성 완료")
        chunk_num += 1

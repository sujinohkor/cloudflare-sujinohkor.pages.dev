import requests

OWNER = "sujinohkor"
REPO = "cloudflare-sujinohkor.pages.dev"
BRANCH = "main"
TARGET_DIR = "codes/hsk-tts/"

url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1"

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

print("GitHub Tree 조회 중...")

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

data = response.json()

# 전체 Tree가 잘리지 않았는지 확인
if data.get("truncated"):
    raise RuntimeError(
        "GitHub Tree 응답이 잘렸습니다. "
        "파일 수가 API 조회 한도를 초과했을 가능성이 있습니다."
    )

# hsk-tts 폴더의 MP3만 필터링
files = [
    item
    for item in data["tree"]
    if item.get("type") == "blob"
    and item.get("path", "").startswith(TARGET_DIR)
    and item.get("path", "").lower().endswith(".mp3")
]

count = len(files)
total_bytes = sum(item.get("size", 0) for item in files)

# 단위 변환
total_kb = total_bytes / 1024
total_mb = total_bytes / (1024 ** 2)
total_gb = total_bytes / (1024 ** 3)

average_bytes = total_bytes / count if count else 0
average_kb = average_bytes / 1024

sizes = [item.get("size", 0) for item in files]

minimum = min(sizes) if sizes else 0
maximum = max(sizes) if sizes else 0

print()
print("=" * 60)
print("GitHub / codes/hsk-tts 분석 결과")
print("=" * 60)

print(f"MP3 파일 수       : {count:,} 개")
print(f"총 용량           : {total_bytes:,} bytes")
print(f"총 용량           : {total_kb:,.2f} KB")
print(f"총 용량           : {total_mb:,.2f} MB")
print(f"총 용량           : {total_gb:,.4f} GB")

print()
print(f"평균 파일 크기    : {average_bytes:,.0f} bytes")
print(f"평균 파일 크기    : {average_kb:,.2f} KB")
print(f"최소 파일 크기    : {minimum:,} bytes")
print(f"최대 파일 크기    : {maximum:,} bytes")

print()
print(f"Tree 항목 전체    : {len(data['tree']):,} 개")
print(f"Tree truncated     : {data.get('truncated', False)}")

print("=" * 60)
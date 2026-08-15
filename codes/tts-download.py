import json
import os
import requests
import time

# Configuration
JSON_URL = "https://raw.githubusercontent.com/sujinohkor/cloudflare-sujinohkor.pages.dev/main/codes/hsk/hsk-combined-words.json"
OUTPUT_DIR = "hsk_tts_audio"

def download_tts():
    # 1. Fetch the JSON data
    print("Fetching JSON data...")
    response = requests.get(JSON_URL)
    if response.status_code != 200:
        print(f"Failed to fetch JSON: {response.status_code}")
        return
    
    data = response.json()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. Iterate and download
    session = requests.Session()
    total = len(data)
    print(f"Starting download for {total} words...")
    
    count = 0
    for word in data.keys():
        try:
            # TTS API URL
            tts_url = f"https://api.wohuimandarin.com/nls/tts?text={word}"
            
            # Request audio
            audio_response = session.get(tts_url, stream=True, timeout=10)
            
            if audio_response.status_code == 200:
                file_path = os.path.join(OUTPUT_DIR, f"{word}.mp3")
                with open(file_path, "wb") as f:
                    for chunk in audio_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                count += 1
            else:
                print(f"Failed to download '{word}': {audio_response.status_code}")
            
            if count % 50 == 0:
                print(f"Progress: {count}/{total}...")
                
        except Exception as e:
            print(f"Error downloading '{word}': {e}")
            
    print(f"Download completed! Total files saved: {count} in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    download_tts()

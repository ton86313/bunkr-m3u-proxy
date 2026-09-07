import re
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Universal Resolver")

# ปลอมแปลง Header ให้เหมือน Chrome เบราว์เซอร์จริงที่สุดเพื่อหลบ Cloudflare
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://bunkr.ws/",
}


@app.get("/bunkr")
def get_bunkr_stream(url: str = Query(..., description="URL Bunkr")):
    try:
        session = requests.Session()
        res = session.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        html = res.text

        # 1. ค้นหาจาก HTML Tags (<video>, <source>, <a>)
        soup = BeautifulSoup(html, "html.parser")

        # หาจากแท็ก <source src="..."> หรือ <video src="...">
        for tag in soup.find_all(["source", "video", "a"]):
            src = tag.get("src") or tag.get("href")
            if src and any(
                ext in src.lower() for ext in [".mp4", ".m3u8", ".ts", ".mkv"]
            ):
                if src.startswith("//"):
                    src = "https:" + src
                return RedirectResponse(url=src, status_code=302)

        # 2. ค้นหาจาก JavaScript / Regex (กรณีซ่อนลิงก์ในสคริปต์)
        patterns = [
            r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts|mkv)[^\s"\'<>]*',
            r'https?://media-files[^\s"\'<>]+',
            r'https?://[^\s"\'<>]+\.bunkr\.[^\s"\'<>]+',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                direct_url = matches[0].rstrip('"\';>')
                return RedirectResponse(url=direct_url, status_code=302)

        # 3. กรณีเป็นหน้า Embed/Iframe ให้ลองแกะ Iframe ถัดไป
        iframes = soup.find_all("iframe")
        for iframe in iframes:
            iframe_src = iframe.get("src")
            if iframe_src:
                if iframe_src.startswith("//"):
                    iframe_src = "https:" + iframe_src
                sub_res = session.get(iframe_src, headers=HEADERS, timeout=10)
                sub_matches = re.findall(
                    r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts)[^\s"\'<>]*',
                    sub_res.text,
                    re.IGNORECASE,
                )
                if sub_matches:
                    return RedirectResponse(
                        url=sub_matches[0].rstrip('"\';>'), status_code=302
                    )

        raise HTTPException(
            status_code=404, detail="ไม่พบไฟล์สื่อในหน้าเว็บ Bunkr นี้"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

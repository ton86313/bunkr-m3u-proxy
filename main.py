import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Direct Resolver")

# ใช้ Header ของ Browser เต็มรูปแบบพร้อมรองรับการถอดรหัส Gzip/Brotli
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


@app.get("/bunkr")
def get_bunkr_stream(url: str = Query(..., description="URL Bunkr")):
    try:
        session = requests.Session()

        # เปลี่ยนโดเมน .ws / .ru ให้เป็นโดเมนหลักปัจจุบันเพื่อหลบ Timeout
        target_url = url.replace("bunkr.ws", "bunkr.black").replace(
            "bunkr.ru", "bunkr.black"
        )

        res = session.get(target_url, headers=HEADERS, timeout=8)
        res.raise_for_status()
        html = res.text

        # 1. ค้นหา Media Link โดยตรง (.mp4, .m3u8, .ts, .mkv)
        match = re.search(
            r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts|mkv)[^\s"\'<>]*',
            html,
            re.IGNORECASE,
        )

        # 2. ค้นหา CDN Server (media-files / cdn)
        if not match:
            match = re.search(
                r'https?://(?:media-files|[^\s"\'<>]+\.bunkr)[^\s"\'<>]+',
                html,
                re.IGNORECASE,
            )

        if match:
            direct_url = match.group(0).rstrip('"\';>')
            return RedirectResponse(url=direct_url, status_code=302)

        raise HTTPException(
            status_code=404, detail="ไม่พบไฟล์สื่อในหน้าเว็บ Bunkr นี้"
        )

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Bunkr Cloudflare Blocked - Timeout Connection",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

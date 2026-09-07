import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Universal Resolver")

# Bunkr ต้องการ User-Agent และ Referer แบบเฉพาะเจาะจง
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://bunkr.ws/",
}


@app.get("/bunkr")
def get_bunkr_stream(url: str = Query(..., description="URL Bunkr")):
    try:
        # 1. ยิง Request ดึง HTML หน้าเว็บ Bunkr
        res = requests.get(url, headers=HEADERS, timeout=12)
        res.raise_for_status()
        html = res.text

        # 2. ค้นหาลิงก์ไฟล์วิดีโอโดยตรง (รองรับ Server ใหม่ๆ เช่น cdnX.bunkr / media-files / .mp4 / .m3u8)
        matches = re.findall(
            r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts|mkv)[^\s"\'<>]*',
            html,
            re.IGNORECASE,
        )

        if not matches:
            # ค้นหา Pattern สำรองกรณี Bunkr ซ่อนลิงก์ใน src หรือ source tag
            matches = re.findall(
                r'(?:src|href|file)["\']?:\s*["\']?(https?://[^\s"\'<>]+)',
                html,
                re.IGNORECASE,
            )

        if matches:
            # คัดเฉพาะลิงก์ที่เป็นไฟล์สื่อ
            valid_urls = [
                m
                for m in matches
                if any(ext in m.lower() for ext in [".mp4", ".m3u8", ".ts"])
            ]
            direct_url = valid_urls[0] if valid_urls else matches[0]

            # ทำความสะอาด URL ลบอักขระส่วนเกิน
            direct_url = direct_url.rstrip('"\';>')
            print(f"[FOUND STREAM]: {direct_url}")

            # Redirect ส่งตรงวิดีโอให้เล่นทันที
            return RedirectResponse(url=direct_url, status_code=302)

        raise HTTPException(
            status_code=404, detail="ไม่พบไฟล์สื่อในหน้าเว็บ Bunkr นี้"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

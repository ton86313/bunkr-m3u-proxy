import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Bypass Proxy")

# ใช้ Headers ที่จำลองมาจาก Browser จริงบน Desktop
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://bunkr.black/",
}


@app.get("/bunkr")
def get_bunkr_stream(url: str = Query(..., description="URL Bunkr")):
    try:
        # ใช้ Session เพื่อรักษา Cookie/Connection
        session = requests.Session()
        session.headers.update(HEADERS)

        res = session.get(url, timeout=12, allow_redirects=True)
        res.raise_for_status()
        html = res.text

        # ค้นหาลิงก์วิดีโอโดยตรง (.mp4, .m3u8, .ts หรือลิงก์ media-files/cdn)
        matches = re.findall(
            r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts|mkv)[^\s"\'<>]*',
            html,
            re.IGNORECASE,
        )

        if not matches:
            matches = re.findall(
                r'(?:src|href|file)["\']?:\s*["\']?(https?://[^\s"\'<>]+)',
                html,
                re.IGNORECASE,
            )

        if matches:
            valid_urls = [
                m
                for m in matches
                if any(
                    ext in m.lower()
                    for ext in [".mp4", ".m3u8", ".ts", "get-media"]
                )
            ]
            direct_url = valid_urls[0] if valid_urls else matches[0]
            direct_url = direct_url.rstrip('"\';>')

            return RedirectResponse(url=direct_url, status_code=302)

        raise HTTPException(
            status_code=404, detail="ไม่พบไฟล์สื่อในหน้าเว็บ Bunkr"
        )

    except requests.exceptions.HTTPError as err:
        raise HTTPException(
            status_code=err.response.status_code, detail=f"Bunkr Blocked: {err}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

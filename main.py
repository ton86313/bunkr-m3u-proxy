import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Fast Resolver")

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
        # จำกัด Timeout เพียง 5 วินาที เพื่อไม่ให้ Render ค้างจนเกิด Error 522
        res = requests.get(url, headers=HEADERS, timeout=5)
        res.raise_for_status()
        html = res.text

        # ค้นหา Direct URL วิดีโอ (.mp4, .m3u8, .ts) แบบรวดเร็วด้วย Regex
        match = re.search(
            r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|ts|mkv)[^\s"\'<>]*',
            html,
            re.IGNORECASE,
        )

        if not match:
            # สำรอง ค้นหาโดเมนตระกูล cdn หรือ media-files ของ bunkr
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
            detail="Bunkr ตอบสนองช้าเกินไป กรุณากดลองใหม่อีกครั้ง",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

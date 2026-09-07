import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import requests

app = FastAPI(title="Bunkr Auto Resolver for WishPlay")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://bunkr.ws/",
}


@app.get("/bunkr")
def get_bunkr_stream(url: str = Query(..., description="URL หน้า Bunkr")):
    """รับ URL Bunkr -> แกะหาไฟล์ .mp4 / CDN ล่าสุด -> Redirect ไปเล่นใน WishPlay"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        html = res.text

        # ค้นหา Direct Link ไฟล์สื่อของ Bunkr (เช่น media-files.bunkr.ru หรือ cdn...bunkr.../....mp4)
        match = re.search(
            r'https://[^\s"\']+\.bunkr\.[^\s"\']+\.mp4[^\s"\']*', html
        ) or re.search(
            r'https://media-files[^\s"\']+\.mp4[^\s"\']*', html
        )

        if not match:
            # ค้นหา pattern สำรองกรณีเปลี่ยนโดเมน CDN
            match = re.search(r'https://[^\s"\']+\.mp4\?[^\s"\']+', html)

        if match:
            direct_url = match.group(0)
            return RedirectResponse(url=direct_url, status_code=302)

        raise HTTPException(
            status_code=404, detail="ไม่พบไฟล์วิดีโอในหน้า Bunkr นี้"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการแกะลิงก์: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
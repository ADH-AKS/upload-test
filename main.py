import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data"))
MAX_BYTES = int(os.getenv("MAX_BYTES", str(50 * 1024 * 1024)))  # 50MB default

app = FastAPI(title="Simple Upload API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Basic content-length guard (best-effort; some clients may not send it)
    if file.size is not None and file.size > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Preserve original extension if present
    orig_name = file.filename or "upload.bin"
    ext = Path(orig_name).suffix
    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / new_name

    # Stream to disk in chunks
    written = 0
    with dest.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_BYTES:
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)

    return {
        "stored_as": new_name,
        "original_name": orig_name,
        "bytes": written,
        "path": str(dest),
    }

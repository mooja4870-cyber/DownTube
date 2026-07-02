"""DownTube — 유튜브 영상/재생목록/채널 다운로드 웹 앱 (mp4/mp3)."""

import hashlib
import hmac
import os
import shutil
import threading
import time
import uuid
import zipfile
from pathlib import Path
from urllib.parse import quote

import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

PASSWORD = os.environ.get("DOWNTUBE_PASSWORD", "downtube1234")
_SECRET = hashlib.sha256(f"downtube-salt::{PASSWORD}".encode()).digest()
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

app = FastAPI(title="DownTube")

jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


def _token() -> str:
    return hmac.new(_SECRET, b"downtube-auth", hashlib.sha256).hexdigest()


def check_auth(request: Request) -> None:
    supplied = request.cookies.get("dt_token") or request.query_params.get("token")
    if not supplied or not hmac.compare_digest(supplied, _token()):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")


class LoginReq(BaseModel):
    password: str


class DownloadReq(BaseModel):
    url: str
    fmt: str = "mp4"      # mp4 | mp3
    quality: str = "best"  # best | 1080 | 720 | 480


def _final_files(outdir: Path) -> list[str]:
    skip = {".part", ".ytdl", ".tmp", ".webp", ".json"}
    return sorted(
        f.name for f in outdir.iterdir()
        if f.is_file() and f.suffix.lower() not in skip and not f.name.startswith(".")
    )


def run_download(job_id: str, url: str, fmt: str, quality: str) -> None:
    job = jobs[job_id]
    outdir = DOWNLOAD_DIR / job_id
    outdir.mkdir(parents=True, exist_ok=True)
    done_ids: set[str] = set()

    def hook(d: dict) -> None:
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            got = d.get("downloaded_bytes") or 0
            job["current_file"] = Path(d.get("filename") or "").name
            job["file_progress"] = round(got / total * 100, 1) if total else 0
        elif d["status"] == "finished":
            vid = (d.get("info_dict") or {}).get("id")
            if vid:
                done_ids.add(vid)
                job["completed"] = len(done_ids)
            job["file_progress"] = 100

    def pp_hook(d: dict) -> None:
        if d["status"] == "started":
            job["message"] = "변환 중..."
        elif d["status"] == "finished":
            job["message"] = ""

    try:
        # 제목/영상 수를 빠르게 파악 (재생목록·채널은 flat 추출)
        with yt_dlp.YoutubeDL(
            {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
        ) as probe:
            info = probe.extract_info(url, download=False)
        if info and info.get("_type") == "playlist":
            entries = [e for e in (info.get("entries") or []) if e]
            job["title"] = info.get("title") or "재생목록"
            job["total"] = info.get("playlist_count") or len(entries) or 1
        else:
            job["title"] = (info or {}).get("title") or url
            job["total"] = 1
        job["status"] = "downloading"

        ydl_opts: dict = {
            "outtmpl": str(outdir / "%(title).150B [%(id)s].%(ext)s"),
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
            "ignoreerrors": "only_download",
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": FFMPEG,
        }
        if fmt == "mp3":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            h = "" if quality == "best" else f"[height<={quality}]"
            ydl_opts["format"] = f"bv*{h}[ext=mp4]+ba[ext=m4a]/b{h}[ext=mp4]/b{h}/b"
            ydl_opts["merge_output_format"] = "mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = _final_files(outdir)
        if not files:
            raise RuntimeError("다운로드된 파일이 없습니다. URL을 확인해 주세요.")
        job["files"] = files
        job["completed"] = job["total"]
        job["status"] = "done"
    except Exception as exc:  # noqa: BLE001 — 작업 실패 사유를 UI로 전달
        job["status"] = "error"
        job["error"] = str(exc)[:500]


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((BASE_DIR / "static" / "index.html").read_text(encoding="utf-8"))


@app.post("/api/login")
def login(body: LoginReq) -> JSONResponse:
    if body.password != PASSWORD:
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다")
    resp = JSONResponse({"ok": True})
    resp.set_cookie("dt_token", _token(), max_age=30 * 24 * 3600, samesite="lax")
    return resp


@app.post("/api/download")
def api_download(req: DownloadReq, request: Request) -> dict:
    check_auth(request)
    if not req.url.strip().lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="올바른 URL을 입력해 주세요")
    if req.fmt not in ("mp4", "mp3"):
        raise HTTPException(status_code=400, detail="지원하지 않는 형식입니다")
    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "url": req.url.strip(),
            "fmt": req.fmt,
            "quality": req.quality,
            "status": "preparing",
            "title": "",
            "total": 0,
            "completed": 0,
            "current_file": "",
            "file_progress": 0,
            "message": "",
            "files": [],
            "error": "",
            "created": time.time(),
        }
    threading.Thread(
        target=run_download, args=(job_id, req.url.strip(), req.fmt, req.quality), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/api/jobs")
def api_jobs(request: Request) -> list[dict]:
    check_auth(request)
    with jobs_lock:
        return sorted(jobs.values(), key=lambda j: j["created"], reverse=True)


@app.delete("/api/jobs/{job_id}")
def api_delete_job(job_id: str, request: Request) -> dict:
    check_auth(request)
    with jobs_lock:
        job = jobs.get(job_id)
        if job and job["status"] in ("done", "error"):
            jobs.pop(job_id)
            shutil.rmtree(DOWNLOAD_DIR / job_id, ignore_errors=True)
            return {"ok": True}
    raise HTTPException(status_code=400, detail="진행 중인 작업은 삭제할 수 없습니다")


def _safe_job_file(job_id: str, filename: str) -> Path:
    outdir = (DOWNLOAD_DIR / job_id).resolve()
    path = (outdir / filename).resolve()
    if not path.is_file() or outdir not in path.parents:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return path


@app.get("/files/{job_id}/{filename:path}")
def get_file(job_id: str, filename: str, request: Request) -> FileResponse:
    check_auth(request)
    path = _safe_job_file(job_id, filename)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.get("/api/jobs/{job_id}/zip")
def get_zip(job_id: str, request: Request) -> FileResponse:
    check_auth(request)
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="완료된 작업이 아닙니다")
    outdir = DOWNLOAD_DIR / job_id
    zip_path = DOWNLOAD_DIR / f"{job_id}.zip"
    if not zip_path.exists():
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for name in job["files"]:
                zf.write(outdir / name, arcname=name)
    title = (job["title"] or "downtube").strip()[:80]
    return FileResponse(zip_path, filename=f"{title}.zip", media_type="application/zip")

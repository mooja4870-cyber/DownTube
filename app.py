"""DownTube — 유튜브 탐색·검색 후 선택한 영상을 mp4/mp3로 다운로드하는 웹 앱."""

import hashlib
import re
import shutil
import threading
import time
import uuid
import zipfile
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# 작업 목록은 메모리 기반이라 서버 재시작 후에는 이전 파일에 접근할 수 없음 — 시작 시 정리
for _stale in DOWNLOAD_DIR.iterdir():
    if _stale.is_dir():
        shutil.rmtree(_stale, ignore_errors=True)
    elif _stale.suffix == ".zip":
        _stale.unlink(missing_ok=True)

FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,20}$")

app = FastAPI(title="DownTube")

jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()

# 검색 결과 캐시: {"query::count": (timestamp, results)}
_search_cache: dict[str, tuple[float, list]] = {}
_search_lock = threading.Lock()
SEARCH_TTL = 600


class DownloadReq(BaseModel):
    id: str
    title: str = ""
    channel: str = ""
    fmt: str = "mp4"      # mp4 | mp3
    quality: str = "best"  # best | 1080 | 720 | 480


def _final_files(outdir: Path) -> list[str]:
    skip = {".part", ".ytdl", ".tmp", ".webp", ".json"}
    return sorted(
        f.name for f in outdir.iterdir()
        if f.is_file() and f.suffix.lower() not in skip and not f.name.startswith(".")
    )


def run_download(job_id: str, video_id: str, fmt: str, quality: str) -> None:
    job = jobs[job_id]
    url = f"https://www.youtube.com/watch?v={video_id}"
    outdir = DOWNLOAD_DIR / job_id
    outdir.mkdir(parents=True, exist_ok=True)

    def hook(d: dict) -> None:
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            got = d.get("downloaded_bytes") or 0
            job["file_progress"] = round(got / total * 100, 1) if total else 0
        elif d["status"] == "finished":
            job["file_progress"] = 100

    def pp_hook(d: dict) -> None:
        if d["status"] == "started":
            job["message"] = "변환 중..."
        elif d["status"] == "finished":
            job["message"] = ""

    try:
        ydl_opts: dict = {
            "outtmpl": str(outdir / "%(title).150B [%(id)s].%(ext)s"),
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
            "noplaylist": True,
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

        job["status"] = "downloading"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if info and not job["title"]:
            job["title"] = info.get("title") or url

        files = _final_files(outdir)
        if not files:
            raise RuntimeError("다운로드된 파일이 없습니다.")
        job["files"] = files
        job["status"] = "done"
    except Exception as exc:  # noqa: BLE001 — 작업 실패 사유를 UI로 전달
        job["status"] = "error"
        job["error"] = str(exc)[:500]


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((BASE_DIR / "static" / "index.html").read_text(encoding="utf-8"))


@app.get("/api/search")
def api_search(q: str, count: int = 18) -> list[dict]:
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="검색어를 입력해 주세요")
    n = max(1, min(count, 50))
    key = f"{q}::{n}"
    now = time.time()
    with _search_lock:
        hit = _search_cache.get(key)
        if hit and now - hit[0] < SEARCH_TTL:
            return hit[1]

    with yt_dlp.YoutubeDL(
        {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    ) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{q}", download=False)

    results = []
    for e in (info or {}).get("entries") or []:
        if not e or not e.get("id"):
            continue
        results.append({
            "id": e["id"],
            "title": e.get("title") or "",
            "channel": e.get("channel") or e.get("uploader") or "",
            "duration": e.get("duration"),
            "views": e.get("view_count"),
            "thumb": f"https://i.ytimg.com/vi/{e['id']}/mqdefault.jpg",
        })
    with _search_lock:
        _search_cache[key] = (now, results)
    return results


@app.post("/api/download")
def api_download(req: DownloadReq) -> dict:
    if not VIDEO_ID_RE.match(req.id):
        raise HTTPException(status_code=400, detail="올바르지 않은 영상 ID입니다")
    if req.fmt not in ("mp4", "mp3"):
        raise HTTPException(status_code=400, detail="지원하지 않는 형식입니다")
    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "video_id": req.id,
            "fmt": req.fmt,
            "quality": req.quality,
            "status": "preparing",
            "title": req.title.strip(),
            "channel": req.channel.strip(),
            "file_progress": 0,
            "message": "",
            "files": [],
            "error": "",
            "created": time.time(),
        }
    threading.Thread(
        target=run_download, args=(job_id, req.id, req.fmt, req.quality), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/api/jobs")
def api_jobs() -> list[dict]:
    with jobs_lock:
        return sorted(jobs.values(), key=lambda j: j["created"], reverse=True)


@app.delete("/api/jobs/{job_id}")
def api_delete_job(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        if job and job["status"] in ("done", "error"):
            jobs.pop(job_id)
            shutil.rmtree(DOWNLOAD_DIR / job_id, ignore_errors=True)
            (DOWNLOAD_DIR / f"{job_id}.zip").unlink(missing_ok=True)
            for stale in DOWNLOAD_DIR.glob("multi_*.zip"):
                stale.unlink(missing_ok=True)
            return {"ok": True}
    raise HTTPException(status_code=400, detail="진행 중인 작업은 삭제할 수 없습니다")


def _safe_job_file(job_id: str, filename: str) -> Path:
    outdir = (DOWNLOAD_DIR / job_id).resolve()
    path = (outdir / filename).resolve()
    if not path.is_file() or outdir not in path.parents:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return path


@app.get("/files/{job_id}/{filename:path}")
def get_file(job_id: str, filename: str) -> FileResponse:
    path = _safe_job_file(job_id, filename)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.get("/api/zip")
def get_multi_zip(ids: str) -> FileResponse:
    job_ids = [i.strip() for i in ids.split(",") if i.strip()]
    with jobs_lock:
        picked = [jobs[i] for i in job_ids if i in jobs and jobs[i]["status"] == "done"]
    if not picked:
        raise HTTPException(status_code=404, detail="완료된 작업이 없습니다")
    key = hashlib.sha256(",".join(sorted(j["id"] for j in picked)).encode()).hexdigest()[:16]
    zip_path = DOWNLOAD_DIR / f"multi_{key}.zip"
    if not zip_path.exists():
        used: set[str] = set()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for j in picked:
                for name in j["files"]:
                    arc, n = name, 1
                    while arc in used:
                        p = Path(name)
                        arc = f"{p.stem} ({n}){p.suffix}"
                        n += 1
                    used.add(arc)
                    zf.write(DOWNLOAD_DIR / j["id"] / name, arcname=arc)
    return FileResponse(zip_path, filename="DownTube_모음.zip", media_type="application/zip")


@app.get("/api/jobs/{job_id}/zip")
def get_zip(job_id: str) -> FileResponse:
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

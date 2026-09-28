"""YouTube Ambient Content Factory — FastAPI backend.

Manages 3 channels (noadsNoise, Noadscolors, Noadshertz): content matrix,
FFmpeg production pipeline, SEO metadata, and YouTube OAuth upload.
"""
from __future__ import annotations

import asyncio
import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

import factory
import youtube_service as yt
from metadata import generate_metadata
from presets import CHANNELS as CH, duration_title as DT
from factory import RENDER_CAP_SECONDS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("factory")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="Ambient Content Factory")
api = APIRouter(prefix="/api")

STAGES_LONG = ["metadata", "rendering", "thumbnail", "done"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────── Models ────────────────────────────────────
class JobCreate(BaseModel):
    channel_key: str
    variant: str
    format: str = "long"          # long | short
    duration_minutes: int
    privacy_status: str = "private"
    auto_upload: bool = False


class ConceptUpdate(BaseModel):
    concept: str


class YTSettings(BaseModel):
    client_id: str
    client_secret: str


# ─────────────────────────────── Helpers ───────────────────────────────────
async def add_log(msg: str, job_id: Optional[str] = None, level: str = "INFO", channel_key: Optional[str] = None):
    entry = {"t": now_iso(), "level": level, "msg": msg, "job_id": job_id, "channel_key": channel_key}
    await db.logs.insert_one(entry)
    if job_id:
        await db.jobs.update_one({"id": job_id}, {"$push": {"logs": {"t": entry["t"], "msg": msg}}})


def clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


async def seed():
    if await db.channels.count_documents({}) == 0:
        for key, ch in CH.items():
            await db.channels.insert_one({
                "key": key, "name": ch["name"], "handle": ch["handle"], "type": ch["type"],
                "focus": ch["focus"], "accent": ch["accent"], "tagline": ch["tagline"],
                "concept": ch["concept"], "connected": False, "youtube_channel_id": None,
                "stats": {"subscribers": 0, "views": 0, "videos": 0},
                "created_at": now_iso(),
            })
        logger.info("Seeded 3 channels")

    if await db.matrix.count_documents({}) == 0:
        cells = []
        for key, ch in CH.items():
            for variant, vmeta in ch["variants"].items():
                for minutes in ch["durations"]:
                    label = vmeta["label"]
                    cells.append({
                        "id": str(uuid.uuid4()), "channel_key": key, "variant": variant,
                        "variant_label": label, "format": "long", "duration_minutes": minutes,
                        "audio_type": ch["type"], "status": "missing", "job_id": None,
                        "filled_at": None, "created_at": now_iso(),
                    })
        if cells:
            await db.matrix.insert_many(cells)
        logger.info("Seeded %d matrix cells", len(cells))


async def get_yt_settings() -> Optional[dict]:
    env_id = os.environ.get("GOOGLE_CLIENT_ID")
    env_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if env_id and env_secret:
        return {"client_id": env_id, "client_secret": env_secret}
    s = await db.settings.find_one({"key": "youtube"})
    if s and s.get("client_id") and s.get("client_secret"):
        return {"client_id": s["client_id"], "client_secret": s["client_secret"]}
    return None


# ─────────────────────────────── Worker ────────────────────────────────────
async def process_job(job: dict):
    jid = job["id"]
    spec = {
        "channel_key": job["channel_key"], "variant": job["variant"],
        "format": job["format"], "duration_minutes": job["duration_minutes"],
        "render_seconds": min(job["duration_minutes"] * 60, RENDER_CAP_SECONDS),
    }
    log = lambda m: asyncio.create_task(add_log(m, jid, channel_key=job["channel_key"]))  # noqa

    async def set_stage(stage, progress, status="processing"):
        await db.jobs.update_one({"id": jid}, {"$set": {"stage": stage, "progress": progress,
                                                         "status": status, "updated_at": now_iso()}})

    try:
        await set_stage("rendering", 25)
        await add_log(f"Rendering {job['variant']} ({DT(job['duration_minutes'])})", jid, channel_key=job["channel_key"])
        video_path = await asyncio.to_thread(factory.render_video, spec, jid,
                                             lambda m: logger.info(m))
        if not video_path:
            raise RuntimeError("FFmpeg render failed")
        await db.jobs.update_one({"id": jid}, {"$set": {"video_path": video_path}})
        await add_log("Video render complete", jid, channel_key=job["channel_key"])

        await set_stage("thumbnail", 65)
        thumb_path = await asyncio.to_thread(factory.render_thumbnail, spec, jid, lambda m: logger.info(m))
        await db.jobs.update_one({"id": jid}, {"$set": {"thumb_path": thumb_path}})
        await add_log("Thumbnail generated", jid, channel_key=job["channel_key"])

        # mark matrix cell filled
        if job.get("matrix_cell_id"):
            await db.matrix.update_one({"id": job["matrix_cell_id"]},
                                       {"$set": {"status": "filled", "job_id": jid, "filled_at": now_iso()}})

        # optional auto upload
        uploaded = False
        if job.get("auto_upload"):
            ok = await try_upload(jid)
            uploaded = ok
        if not uploaded:
            await set_stage("done", 100, "completed")
            await add_log("Job completed", jid, level="SUCCESS", channel_key=job["channel_key"])
    except Exception as exc:  # noqa
        await db.jobs.update_one({"id": jid}, {"$set": {"status": "failed", "error": str(exc),
                                                        "stage": "failed", "updated_at": now_iso()}})
        if job.get("matrix_cell_id"):
            await db.matrix.update_one({"id": job["matrix_cell_id"]}, {"$set": {"status": "missing", "job_id": None}})
        await add_log(f"FAILED: {exc}", jid, level="ERROR", channel_key=job["channel_key"])


async def try_upload(job_id: str) -> bool:
    job = await db.jobs.find_one({"id": job_id})
    if not job or not job.get("video_path"):
        return False
    channel = await db.channels.find_one({"key": job["channel_key"]})
    settings = await get_yt_settings()
    if not channel or not channel.get("connected") or not settings:
        await add_log("Upload skipped: channel not connected", job_id, level="WARN",
                      channel_key=job["channel_key"])
        return False
    token = await db.oauth_tokens.find_one({"channel_key": job["channel_key"]})
    if not token:
        return False
    await db.jobs.update_one({"id": job_id}, {"$set": {"status": "uploading", "stage": "uploading",
                                                       "progress": 85, "updated_at": now_iso()}})
    await add_log("Uploading to YouTube…", job_id, channel_key=job["channel_key"])
    try:
        result = await asyncio.to_thread(
            yt.upload_video, token, settings["client_id"], settings["client_secret"],
            file_path=job["video_path"], title=job["title"], description=job["description"],
            tags=job.get("tags", []), privacy=job.get("privacy_status", "private"),
            thumb_path=job.get("thumb_path"),
        )
        await db.jobs.update_one({"id": job_id}, {"$set": {
            "status": "completed", "stage": "done", "progress": 100,
            "youtube_video_id": result["video_id"], "uploaded_at": now_iso(), "updated_at": now_iso()}})
        await add_log(f"Uploaded! video id={result['video_id']}", job_id, level="SUCCESS",
                      channel_key=job["channel_key"])
        return True
    except Exception as exc:  # noqa
        await db.jobs.update_one({"id": job_id}, {"$set": {"status": "completed", "stage": "done",
                                                          "progress": 100, "error": f"upload: {exc}"}})
        await add_log(f"Upload error: {exc}", job_id, level="ERROR", channel_key=job["channel_key"])
        return False


async def worker_loop():
    await asyncio.sleep(2)
    while True:
        try:
            job = await db.jobs.find_one({"status": "queued"}, sort=[("created_at", 1)])
            if job:
                await db.jobs.update_one({"id": job["id"]}, {"$set": {"status": "processing"}})
                await process_job(job)
            else:
                await asyncio.sleep(2)
        except Exception as exc:  # noqa
            logger.error("worker error: %s", exc)
            await asyncio.sleep(3)


# ─────────────────────────────── Endpoints ─────────────────────────────────
@api.get("/health")
async def health():
    return {"status": "ok", "ffmpeg": bool(os.popen("which ffmpeg").read().strip())}


@api.get("/presets")
async def presets():
    out = {}
    for key, ch in CH.items():
        out[key] = {
            "name": ch["name"], "type": ch["type"], "accent": ch["accent"], "tagline": ch["tagline"],
            "durations": ch["durations"],
            "variants": [{"key": vk, "label": vv["label"],
                          "extra": vv.get("purpose") or vv.get("hex", "")}
                         for vk, vv in ch["variants"].items()],
        }
    return out


@api.get("/channels")
async def list_channels():
    channels = await db.channels.find({}, {"_id": 0}).to_list(10)
    for ch in channels:
        cells = await db.matrix.find({"channel_key": ch["key"]}).to_list(2000)
        ch["matrix_total"] = len(cells)
        ch["matrix_filled"] = sum(1 for c in cells if c["status"] == "filled")
        ch["matrix_missing"] = sum(1 for c in cells if c["status"] == "missing")
        jobs = await db.jobs.find({"channel_key": ch["key"]}).to_list(5000)
        ch["queue"] = {
            "queued": sum(1 for j in jobs if j["status"] == "queued"),
            "processing": sum(1 for j in jobs if j["status"] in ("processing", "uploading")),
            "completed": sum(1 for j in jobs if j["status"] == "completed"),
            "failed": sum(1 for j in jobs if j["status"] == "failed"),
        }
    return channels


@api.put("/channels/{key}")
async def update_channel(key: str, body: ConceptUpdate):
    r = await db.channels.update_one({"key": key}, {"$set": {"concept": body.concept}})
    if r.matched_count == 0:
        raise HTTPException(404, "Channel not found")
    return {"success": True}


@api.get("/dashboard")
async def dashboard():
    channels = await list_channels()
    all_jobs = await db.jobs.find({}, {"_id": 0}).to_list(10000)
    return {
        "channels": channels,
        "totals": {
            "queued": sum(1 for j in all_jobs if j["status"] == "queued"),
            "processing": sum(1 for j in all_jobs if j["status"] in ("processing", "uploading")),
            "completed": sum(1 for j in all_jobs if j["status"] == "completed"),
            "failed": sum(1 for j in all_jobs if j["status"] == "failed"),
            "jobs_total": len(all_jobs),
        },
    }


@api.get("/matrix")
async def get_matrix(channel: str):
    cells = await db.matrix.find({"channel_key": channel}, {"_id": 0}).to_list(3000)
    cells.sort(key=lambda c: (c["duration_minutes"], c["variant_label"]))
    return cells


async def _create_job(channel_key: str, variant: str, fmt: str, minutes: int,
                      privacy: str, auto_upload: bool, matrix_cell_id: Optional[str] = None) -> dict:
    if channel_key not in CH:
        raise HTTPException(400, "Unknown channel")
    ch = CH[channel_key]
    if variant not in ch["variants"]:
        raise HTTPException(400, "Unknown variant")
    meta = generate_metadata(channel_key, variant, minutes)
    job = {
        "id": str(uuid.uuid4()), "channel_key": channel_key, "channel_type": ch["type"],
        "variant": variant, "variant_label": ch["variants"][variant]["label"],
        "format": fmt, "duration_minutes": minutes, "duration_seconds": minutes * 60,
        "render_seconds": min(minutes * 60, RENDER_CAP_SECONDS),
        "title": meta["title"], "description": meta["description"], "tags": meta["tags"],
        "status": "queued", "stage": "metadata", "progress": 5, "privacy_status": privacy,
        "auto_upload": auto_upload, "matrix_cell_id": matrix_cell_id,
        "video_path": None, "thumb_path": None, "youtube_video_id": None,
        "error": None, "logs": [], "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.jobs.insert_one(job)
    await add_log(f"Job queued: {meta['title'][:60]}", job["id"], channel_key=channel_key)
    return job


@api.post("/jobs")
async def create_job(body: JobCreate):
    cell = await db.matrix.find_one({"channel_key": body.channel_key, "variant": body.variant,
                                     "format": body.format, "duration_minutes": body.duration_minutes})
    cell_id = None
    if cell and cell["status"] == "missing":
        cell_id = cell["id"]
        await db.matrix.update_one({"id": cell_id}, {"$set": {"status": "producing"}})
    job = await _create_job(body.channel_key, body.variant, body.format, body.duration_minutes,
                            body.privacy_status, body.auto_upload, cell_id)
    return clean(job)


@api.post("/matrix/{cell_id}/produce")
async def produce_cell(cell_id: str):
    cell = await db.matrix.find_one({"id": cell_id})
    if not cell:
        raise HTTPException(404, "Cell not found")
    if cell["status"] != "missing":
        raise HTTPException(400, "Cell already produced or in progress")
    await db.matrix.update_one({"id": cell_id}, {"$set": {"status": "producing"}})
    job = await _create_job(cell["channel_key"], cell["variant"], cell["format"],
                            cell["duration_minutes"], "private", False, cell_id)
    return clean(job)


@api.post("/channels/{key}/batch")
async def batch_produce(key: str, limit: int = 5):
    cells = await db.matrix.find({"channel_key": key, "status": "missing"}).to_list(1000)
    cells.sort(key=lambda c: c["duration_minutes"])
    created = 0
    for cell in cells[:limit]:
        await db.matrix.update_one({"id": cell["id"]}, {"$set": {"status": "producing"}})
        await _create_job(cell["channel_key"], cell["variant"], cell["format"],
                          cell["duration_minutes"], "private", False, cell["id"])
        created += 1
    return {"success": True, "queued": created}


@api.get("/jobs")
async def list_jobs(channel: Optional[str] = None, status: Optional[str] = None, limit: int = 100):
    q = {}
    if channel:
        q["channel_key"] = channel
    if status:
        q["status"] = status
    jobs = await db.jobs.find(q, {"_id": 0, "logs": 0, "description": 0}).sort("created_at", -1).to_list(limit)
    return jobs


@api.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@api.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(404, "Job not found")
    await db.jobs.update_one({"id": job_id}, {"$set": {"status": "queued", "stage": "metadata",
                                                       "progress": 5, "error": None, "updated_at": now_iso()}})
    if job.get("matrix_cell_id"):
        await db.matrix.update_one({"id": job["matrix_cell_id"]}, {"$set": {"status": "producing"}})
    return {"success": True}


@api.post("/jobs/{job_id}/upload")
async def upload_job(job_id: str):
    ok = await try_upload(job_id)
    if not ok:
        raise HTTPException(400, "Upload failed or channel not connected")
    return {"success": True}


@api.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if job and job.get("matrix_cell_id"):
        await db.matrix.update_one({"id": job["matrix_cell_id"]},
                                   {"$set": {"status": "missing", "job_id": None}})
    await db.jobs.delete_one({"id": job_id})
    return {"success": True}


@api.get("/media/{job_id}/video")
async def media_video(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job or not job.get("video_path") or not os.path.exists(job["video_path"]):
        raise HTTPException(404, "Video not found")
    return FileResponse(job["video_path"], media_type="video/mp4")


@api.get("/media/{job_id}/thumb")
async def media_thumb(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job or not job.get("thumb_path") or not os.path.exists(job["thumb_path"]):
        raise HTTPException(404, "Thumbnail not found")
    return FileResponse(job["thumb_path"], media_type="image/jpeg")


@api.get("/gallery")
async def gallery(channel: Optional[str] = None):
    q = {"thumb_path": {"$ne": None}, "status": {"$in": ["completed", "uploading"]}}
    if channel:
        q["channel_key"] = channel
    jobs = await db.jobs.find(q, {"_id": 0, "logs": 0, "description": 0}).sort("created_at", -1).to_list(60)
    return jobs


@api.get("/logs")
async def get_logs(limit: int = 80, channel: Optional[str] = None):
    q = {}
    if channel:
        q["channel_key"] = channel
    logs = await db.logs.find(q, {"_id": 0}).sort("t", -1).to_list(limit)
    return list(reversed(logs))


# ── Scheduler ────────────────────────────────────────────────────────────────
class ScheduleCreate(BaseModel):
    channel_key: str
    time_slot: str          # "HH:MM"
    variant: str
    duration_minutes: int
    enabled: bool = True


@api.get("/schedules")
async def list_schedules():
    return await db.schedules.find({}, {"_id": 0}).to_list(200)


@api.post("/schedules")
async def create_schedule(body: ScheduleCreate):
    sched = body.model_dump()
    sched["id"] = str(uuid.uuid4())
    sched["created_at"] = now_iso()
    await db.schedules.insert_one(sched)
    return clean(sched)


@api.put("/schedules/{sid}")
async def toggle_schedule(sid: str):
    s = await db.schedules.find_one({"id": sid})
    if not s:
        raise HTTPException(404, "Not found")
    await db.schedules.update_one({"id": sid}, {"$set": {"enabled": not s.get("enabled", True)}})
    return {"success": True}


@api.delete("/schedules/{sid}")
async def delete_schedule(sid: str):
    await db.schedules.delete_one({"id": sid})
    return {"success": True}


@api.post("/schedules/{sid}/run")
async def run_schedule(sid: str):
    s = await db.schedules.find_one({"id": sid})
    if not s:
        raise HTTPException(404, "Not found")
    job = await _create_job(s["channel_key"], s["variant"], "long", s["duration_minutes"], "private", False)
    return clean(job)


# ── YouTube OAuth ────────────────────────────────────────────────────────────
@api.get("/youtube/status")
async def youtube_status():
    settings = await get_yt_settings()
    channels = await db.channels.find({}, {"_id": 0, "key": 1, "connected": 1,
                                           "youtube_channel_id": 1, "name": 1}).to_list(10)
    return {"configured": settings is not None, "redirect_uri": yt.REDIRECT_URI, "channels": channels}


@api.post("/youtube/settings")
async def youtube_settings(body: YTSettings):
    await db.settings.update_one({"key": "youtube"},
                                 {"$set": {"key": "youtube", "client_id": body.client_id,
                                           "client_secret": body.client_secret}}, upsert=True)
    return {"success": True}


@api.get("/youtube/auth-url")
async def youtube_auth_url(channel: str):
    settings = await get_yt_settings()
    if not settings:
        raise HTTPException(400, "YouTube OAuth not configured")
    if not yt.REDIRECT_URI:
        raise HTTPException(400, "PUBLIC_URL not set on backend")
    url = await asyncio.to_thread(yt.build_auth_url, settings["client_id"], settings["client_secret"], channel)
    return {"auth_url": url}


@api.get("/youtube/callback")
async def youtube_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    frontend = os.environ.get("PUBLIC_URL", "")
    if error or not code or not state:
        return RedirectResponse(f"{frontend}/settings?yt=error")
    settings = await get_yt_settings()
    if not settings:
        return RedirectResponse(f"{frontend}/settings?yt=error")
    try:
        token = await asyncio.to_thread(yt.exchange_code, settings["client_id"], settings["client_secret"], code)
        info = await asyncio.to_thread(yt.get_channel_info, token, settings["client_id"], settings["client_secret"])
        await db.oauth_tokens.update_one({"channel_key": state}, {"$set": {**token, "channel_key": state}}, upsert=True)
        upd = {"connected": True}
        if info:
            upd["youtube_channel_id"] = info["youtube_channel_id"]
            upd["stats"] = {"subscribers": info["subscribers"], "views": info["views"], "videos": info["videos"]}
        await db.channels.update_one({"key": state}, {"$set": upd})
        await add_log(f"YouTube connected for {state}", channel_key=state, level="SUCCESS")
        return RedirectResponse(f"{frontend}/settings?yt=connected")
    except Exception as exc:  # noqa
        logger.error("oauth callback: %s", exc)
        return RedirectResponse(f"{frontend}/settings?yt=error")


@api.post("/channels/{key}/disconnect")
async def disconnect_channel(key: str):
    await db.oauth_tokens.delete_many({"channel_key": key})
    await db.channels.update_one({"key": key}, {"$set": {"connected": False, "youtube_channel_id": None}})
    return {"success": True}


app.include_router(api)
app.add_middleware(
    CORSMiddleware, allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await seed()
    asyncio.create_task(worker_loop())
    logger.info("Factory backend started")


@app.on_event("shutdown")
async def shutdown():
    client.close()

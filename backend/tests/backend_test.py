"""Backend integration tests for Ambient Content Factory."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://content-forge-1726.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# Fallback: read from frontend/.env if not set in env
if not os.environ.get("REACT_APP_BACKEND_URL"):
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    API = f"{BASE_URL}/api"
                    break
    except Exception:
        pass


# ── Health / presets / channels ────────────────────────────────────────────
def test_health():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["ffmpeg"] is True


def test_channels_seeded():
    r = requests.get(f"{API}/channels", timeout=10)
    assert r.status_code == 200
    ch = r.json()
    keys = {c["key"] for c in ch}
    assert {"noadsNoise", "Noadscolors", "Noadshertz"}.issubset(keys)
    for c in ch:
        assert "matrix_total" in c and c["matrix_total"] > 0
        assert "matrix_filled" in c and "matrix_missing" in c
        assert "queue" in c
        for k in ("queued", "processing", "completed", "failed"):
            assert k in c["queue"]


def test_presets():
    r = requests.get(f"{API}/presets", timeout=10)
    assert r.status_code == 200
    data = r.json()
    for key in ("noadsNoise", "Noadscolors", "Noadshertz"):
        assert key in data
        assert isinstance(data[key]["variants"], list) and len(data[key]["variants"]) > 0
        assert isinstance(data[key]["durations"], list) and len(data[key]["durations"]) > 0


def test_matrix_returns_cells():
    r = requests.get(f"{API}/matrix", params={"channel": "noadsNoise"}, timeout=10)
    assert r.status_code == 200
    cells = r.json()
    assert len(cells) > 0
    assert {"id", "channel_key", "variant", "duration_minutes", "status"}.issubset(cells[0].keys())


# ── Job creation + SEO metadata ────────────────────────────────────────────
def test_create_job_returns_seo():
    body = {"channel_key": "Noadscolors", "variant": "blue",
            "format": "long", "duration_minutes": 30}
    r = requests.post(f"{API}/jobs", json=body, timeout=15)
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "queued"
    assert job["title"] and len(job["title"]) > 5
    assert job["description"] and len(job["description"]) > 20
    assert isinstance(job["tags"], list) and len(job["tags"]) > 0
    # cleanup
    requests.delete(f"{API}/jobs/{job['id']}", timeout=10)


def _wait_for_job(jid: str, timeout: int = 90) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        r = requests.get(f"{API}/jobs/{jid}", timeout=10)
        if r.status_code == 200:
            last = r.json()
            if last["status"] in ("completed", "failed"):
                return last
        time.sleep(2)
    return last


# ── End-to-end for all 3 channel types ─────────────────────────────────────
@pytest.mark.parametrize("channel_key,variant", [
    ("noadsNoise", "rain"),
    ("Noadscolors", "blue"),
    ("Noadshertz", "528"),
])
def test_full_render_pipeline(channel_key, variant):
    body = {"channel_key": channel_key, "variant": variant,
            "format": "long", "duration_minutes": 10}
    r = requests.post(f"{API}/jobs", json=body, timeout=15)
    assert r.status_code == 200, r.text
    jid = r.json()["id"]
    final = _wait_for_job(jid, timeout=120)
    assert final.get("status") == "completed", f"job did not complete: {final}"
    assert final.get("progress") == 100
    assert final.get("video_path")
    assert final.get("thumb_path")

    # media endpoints
    rv = requests.get(f"{API}/media/{jid}/video", timeout=20, stream=True)
    assert rv.status_code == 200
    assert rv.headers.get("content-type", "").startswith("video/mp4")
    size = sum(len(chunk) for chunk in rv.iter_content(8192))
    assert size > 1000

    rt = requests.get(f"{API}/media/{jid}/thumb", timeout=20)
    assert rt.status_code == 200
    assert rt.headers.get("content-type", "").startswith("image/")
    assert len(rt.content) > 500


# ── Matrix produce endpoint ────────────────────────────────────────────────
def test_matrix_produce_updates_status():
    # find a missing cell for Noadscolors (short durations, quicker)
    cells = requests.get(f"{API}/matrix", params={"channel": "Noadscolors"}, timeout=10).json()
    missing = [c for c in cells if c["status"] == "missing"]
    if not missing:
        pytest.skip("no missing cells")
    # prefer shortest duration
    missing.sort(key=lambda c: c["duration_minutes"])
    cell = missing[0]
    r = requests.post(f"{API}/matrix/{cell['id']}/produce", timeout=15)
    assert r.status_code == 200
    job = r.json()
    # cell should be producing immediately
    cells2 = requests.get(f"{API}/matrix", params={"channel": "Noadscolors"}, timeout=10).json()
    cell2 = next(c for c in cells2 if c["id"] == cell["id"])
    assert cell2["status"] in ("producing", "filled")
    final = _wait_for_job(job["id"], timeout=120)
    assert final.get("status") == "completed"
    cells3 = requests.get(f"{API}/matrix", params={"channel": "Noadscolors"}, timeout=10).json()
    cell3 = next(c for c in cells3 if c["id"] == cell["id"])
    assert cell3["status"] == "filled"


def test_batch_produce():
    r = requests.post(f"{API}/channels/Noadscolors/batch", params={"limit": 3}, timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["queued"] >= 0  # may be 0 if all cells filled


# ── Filtering / gallery / logs ─────────────────────────────────────────────
def test_jobs_filtering_and_gallery_logs():
    r = requests.get(f"{API}/jobs", params={"channel": "Noadscolors"}, timeout=10)
    assert r.status_code == 200
    for j in r.json():
        assert j["channel_key"] == "Noadscolors"

    r = requests.get(f"{API}/gallery", timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = requests.get(f"{API}/logs", timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Retry + delete ─────────────────────────────────────────────────────────
def test_retry_and_delete_job():
    body = {"channel_key": "Noadscolors", "variant": "red",
            "format": "long", "duration_minutes": 15}
    r = requests.post(f"{API}/jobs", json=body, timeout=15)
    jid = r.json()["id"]
    # retry
    rr = requests.post(f"{API}/jobs/{jid}/retry", timeout=10)
    assert rr.status_code == 200
    # delete
    rd = requests.delete(f"{API}/jobs/{jid}", timeout=10)
    assert rd.status_code == 200
    # verify gone
    r2 = requests.get(f"{API}/jobs/{jid}", timeout=10)
    assert r2.status_code == 404


# ── Scheduler ──────────────────────────────────────────────────────────────
def test_scheduler_crud():
    body = {"channel_key": "Noadscolors", "time_slot": "09:00",
            "variant": "yellow", "duration_minutes": 15, "enabled": True}
    r = requests.post(f"{API}/schedules", json=body, timeout=10)
    assert r.status_code == 200
    sid = r.json()["id"]

    ls = requests.get(f"{API}/schedules", timeout=10).json()
    assert any(s["id"] == sid for s in ls)

    rn = requests.post(f"{API}/schedules/{sid}/run", timeout=15)
    assert rn.status_code == 200
    new_job_id = rn.json()["id"]

    tg = requests.put(f"{API}/schedules/{sid}", timeout=10)
    assert tg.status_code == 200

    dl = requests.delete(f"{API}/schedules/{sid}", timeout=10)
    assert dl.status_code == 200

    # cleanup created job
    requests.delete(f"{API}/jobs/{new_job_id}", timeout=10)


# ── YouTube ────────────────────────────────────────────────────────────────
def test_youtube_status_unconfigured():
    r = requests.get(f"{API}/youtube/status", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "configured" in data
    assert len(data["channels"]) == 3


def test_youtube_settings_and_authurl():
    r = requests.post(f"{API}/youtube/settings",
                      json={"client_id": "TEST_client.apps.googleusercontent.com",
                            "client_secret": "TEST_secret_value"}, timeout=10)
    assert r.status_code == 200
    # after saving, status should be configured
    st = requests.get(f"{API}/youtube/status", timeout=10).json()
    assert st["configured"] is True

    au = requests.get(f"{API}/youtube/auth-url", params={"channel": "noadsNoise"}, timeout=10)
    # may 400 if PUBLIC_URL not set; treat that as valid failure mode
    if au.status_code == 200:
        assert "auth_url" in au.json()
        assert "accounts.google.com" in au.json()["auth_url"]
    else:
        assert au.status_code == 400


def test_upload_gated_without_connection():
    # create a quick job and immediately try to upload — should 400
    body = {"channel_key": "Noadscolors", "variant": "white",
            "format": "long", "duration_minutes": 10}
    j = requests.post(f"{API}/jobs", json=body, timeout=15).json()
    r = requests.post(f"{API}/jobs/{j['id']}/upload", timeout=15)
    assert r.status_code == 400
    requests.delete(f"{API}/jobs/{j['id']}", timeout=10)

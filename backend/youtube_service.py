"""YouTube Data API v3 — OAuth2 (offline) connect + video upload.

Server-side authorization-code flow. Client ID/Secret and the public redirect
URI come from env / the settings collection. All functions here are synchronous
(google-api-python-client) and are called from the async server via to_thread.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")
REDIRECT_URI = f"{PUBLIC_URL}/api/youtube/callback" if PUBLIC_URL else ""


def _client_config(client_id: str, client_secret: str) -> dict:
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def build_auth_url(client_id: str, client_secret: str, state: str) -> str:
    flow = Flow.from_client_config(_client_config(client_id, client_secret), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true",
                                    prompt="consent", state=state)
    return url


def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    flow = Flow.from_client_config(_client_config(client_id, client_secret), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    c = flow.credentials
    return {
        "access_token": c.token,
        "refresh_token": c.refresh_token,
        "expires_at": (c.expiry.replace(tzinfo=timezone.utc).isoformat() if c.expiry else None),
        "scopes": list(c.scopes or SCOPES),
    }


def _credentials(token: dict, client_id: str, client_secret: str) -> Credentials:
    creds = Credentials(
        token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=token.get("scopes", SCOPES),
    )
    if creds.expired or not creds.valid:
        try:
            creds.refresh(GoogleRequest())
        except Exception:
            pass
    return creds


def get_channel_info(token: dict, client_id: str, client_secret: str) -> Optional[dict]:
    creds = _credentials(token, client_id, client_secret)
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
    items = resp.get("items")
    if not items:
        return None
    it = items[0]
    s = it.get("snippet", {})
    st = it.get("statistics", {})
    return {
        "youtube_channel_id": it.get("id"),
        "title": s.get("title"),
        "subscribers": int(st.get("subscriberCount", 0) or 0),
        "views": int(st.get("viewCount", 0) or 0),
        "videos": int(st.get("videoCount", 0) or 0),
        "access_token": creds.token,
    }


def upload_video(token: dict, client_id: str, client_secret: str, *, file_path: str,
                 title: str, description: str, tags: list, privacy: str,
                 thumb_path: Optional[str] = None) -> dict:
    creds = _credentials(token, client_id, client_secret)
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    body = {
        "snippet": {"title": title[:100], "description": description[:5000], "tags": tags[:30], "categoryId": "10"},
        "status": {"privacyStatus": privacy or "private", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _status, response = request.next_chunk()
    video_id = response["id"]
    if thumb_path and os.path.exists(thumb_path):
        try:
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path)).execute()
        except Exception:
            pass
    return {"video_id": video_id, "access_token": creds.token}

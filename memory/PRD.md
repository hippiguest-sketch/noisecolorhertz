# Ambient Content Factory — PRD

## Original Problem Statement
Build an app to manage 3 ambient YouTube channels end-to-end (production, upload,
optimization — fully automatic), based on the user's existing "production factory":
- https://www.youtube.com/@noadsNoise/ (rain/thunder/white/brown/pink noise, black-screen sleep sounds)
- https://www.youtube.com/@Noadscolors/ (solid color screens, chromatherapy, meditation)
- https://www.youtube.com/@Noadshertz/ (healing frequencies / Solfeggio / Hz)

## User Choices
- Scope: ALL of it (production + upload + management pipeline).
- Rendering: FFmpeg (ported from user's existing factory).
- YouTube: OAuth (YouTube Data API v3) integration for real uploads.
- AI: NONE — template-based SEO metadata (user already has a thumbnail generator).

## Architecture
- Frontend: React 19 + react-router + Tailwind + shadcn/ui + framer-motion + sonner (dark command-center UI).
- Backend: FastAPI + MongoDB (motor). Background asyncio worker processes the job queue.
- Media pipeline (backend/factory.py): FFmpeg renders solid-color / black-screen videos with
  anoisesrc noise or sine Hz audio + showwaves overlay; Pillow renders the v6-style thumbnail
  (big duration number, dotted divider, variant lines, red NO ADS badge). Renders capped to ~18s
  preview per job; metadata advertises the full intended duration.
- SEO (backend/metadata.py): multilingual template title/description/tags per channel type.
- Presets (backend/presets.py): 3 channels, noise/color/hz variants, duration ladders.
- YouTube (backend/youtube_service.py): server-side OAuth code flow + videos.insert + thumbnails.set.
- Generated media served via /api/media/{job_id}/{video|thumb}; stored under backend/generated/.

## Personas
- Solo channel operator managing 3 ambient channels who wants one-click, hands-off production + upload.

## Core Requirements (static)
- Multi-channel dashboard with matrix progress + queue stats.
- Content matrix (variant × duration) with one-click produce.
- Production studio (choose channel/variant/duration/format) with live SEO preview.
- Pipeline board with live status/progress + detail modal (video + thumbnail preview).
- Asset gallery, scheduler, live logs.
- YouTube OAuth connect + upload (per channel).

## Implemented (2026-06)
- Full FFmpeg render pipeline for all 3 channel types (noise/color/hz) — verified end-to-end.
- Pillow v6 thumbnail generation with NO ADS badge — verified.
- Template SEO metadata (title/description/tags, multilingual) — verified.
- MongoDB models: channels, matrix, jobs, logs, schedules, oauth_tokens, settings.
- Background worker (queued → rendering → thumbnail → done; optional auto-upload).
- All 8 pages + all /api endpoints. Testing agent: backend 100%, frontend 100% (iteration_1).
- YouTube OAuth code flow implemented + gated behind user-supplied Google Cloud credentials.

## Backlog
- P0: User provides Google Cloud OAuth Client ID/Secret → verify real channel connect + upload.
- P1: Full-length (multi-hour) render path (loop base clip) triggered at upload time.
- P1: Scheduler auto-run via platform cron (currently manual "run now" per slot).
- P2: Shorts pipeline polish (9:16 waveform), analytics sync from YouTube, gradient/breathing color visuals.
- P2: Split server.py (worker + youtube router) once it grows past ~700 lines.

## Notes
- No app login (single-operator tool). ffmpeg installed via apt in the container.
- MOCKED/GATED: real YouTube upload requires user's Google OAuth creds (not configured yet).

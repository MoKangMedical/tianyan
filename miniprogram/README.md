# Tianyan WeChat Mini Program

This directory contains the initial WeChat Mini Program scaffold for Tianyan.

## Current scope

- Home screen for capability overview and API health check
- Case screen for Medislim-style case presentation
- Narration generation wired to `POST /api/v1/media/audio`
- Video generation wired to `POST /api/v1/media/video`
- Report generation contract prepared for `POST /api/v1/report/generate`
- Configurable API base stored in local storage

## Provider split

- Text / analysis / report generation: `DeepSeek V4 Pro`
- Audio narration: `Xiaomi Mimo`

## Open in WeChat DevTools

1. Open WeChat DevTools.
2. Import the `miniprogram` directory as a Mini Program project.
3. Use your own AppID or test AppID.
4. In DevTools, update the request domain whitelist if you use a production API domain.

## Local demo mode

Run:

```bash
python3 mock_backend/server.py
```

Then set the Mini Program API base to:

```text
http://127.0.0.1:8788
```

This local mock returns working demo URLs for:

- `audio_url`
- `video_url`
- `poster_url`

## Backend requirements

The Mini Program expects these endpoints:

- `GET /api/health`
- `POST /api/v1/media/audio`
- `POST /api/v1/media/video`
- `POST /api/v1/report/generate`

The current default API base is the public audio gateway:

- `https://tianyan-api.mokangmedical-dev.workers.dev`

That default is enough for:

- health check
- audio narration

It is not enough for the full Tianyan product flow, DeepSeek-backed report generation, or ComfyUI video generation. For production, replace it with your formal backend domain, for example:

- `https://api.yourdomain.com`

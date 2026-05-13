# Local Mock Backend

This service exists so the WeChat Mini Program can demonstrate:

- DeepSeek text provider status
- local voiceover asset URL
- ComfyUI video asset URL

## Run

```bash
python3 mock_backend/server.py
```

Default address:

```text
http://127.0.0.1:8788
```

## Endpoints

- `GET /api/health`
- `POST /api/v1/report/generate`
- `POST /api/v1/media/audio`
- `POST /api/v1/media/video`

## Static demo assets

- `GET /mock/audio/demo.mp3`
- `GET /mock/video/demo.mp4`
- `GET /mock/video/demo.jpg`

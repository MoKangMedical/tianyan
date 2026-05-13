#!/usr/bin/env python3
"""
Local mock backend for Tianyan WeChat Mini Program demos.

Endpoints:
- GET /api/health
- POST /api/v1/report/generate
- POST /api/v1/media/audio
- POST /api/v1/media/video
- GET /mock/audio/demo.mp3
- GET /mock/video/demo.mp4
- GET /mock/video/demo.jpg
"""

from __future__ import annotations

import argparse
import base64
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


APP_VERSION = "1.0.0"
ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
AUDIO_PATH = ASSETS_DIR / "audio" / "demo.mp3"
VIDEO_PATH = ASSETS_DIR / "video" / "demo.mp4"
POSTER_PATH = ASSETS_DIR / "video" / "demo.jpg"


def load_audio_base64() -> str:
    return base64.b64encode(AUDIO_PATH.read_bytes()).decode("utf-8")


class MockHandler(BaseHTTPRequestHandler):
    server_version = "TianyanMock/1.0"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/mock/audio/demo.mp3":
            self._send_file_headers(AUDIO_PATH, "audio/mpeg")
            return

        if parsed.path == "/mock/video/demo.mp4":
            self._send_file_headers(VIDEO_PATH, "video/mp4")
            return

        if parsed.path == "/mock/video/demo.jpg":
            self._send_file_headers(POSTER_PATH, "image/jpeg")
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._send_json(
                {
                    "status": "healthy",
                    "version": APP_VERSION,
                    "llm": {
                        "provider": "deepseek",
                        "model": "deepseek-v4-pro",
                        "configured": True,
                        "available": True,
                    },
                    "media": {
                        "audio": {
                            "provider": "mimo",
                            "model": "local-voiceover-demo",
                            "configured": True,
                            "available": True,
                        },
                        "video": {
                            "provider": "comfyui",
                            "model": "comfyui-local-demo",
                            "configured": True,
                            "available": True,
                        },
                    },
                }
            )
            return

        if parsed.path == "/mock/audio/demo.mp3":
            self._send_file(AUDIO_PATH, "audio/mpeg")
            return

        if parsed.path == "/mock/video/demo.mp4":
            self._send_file(VIDEO_PATH, "video/mp4")
            return

        if parsed.path == "/mock/video/demo.jpg":
            self._send_file(POSTER_PATH, "image/jpeg")
            return

        self._send_json({"detail": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self._read_json()

        if parsed.path == "/api/v1/report/generate":
            product_name = body.get("product_name") or "Medislim"
            objective = body.get("objective") or "launch"
            title = f"{product_name} 中国{objective}建议"
            summary = (
                f"{product_name} 当前适合以 DeepSeek V4 Pro 生成研究摘要，"
                "再交给本地配音和 ComfyUI 形成演示级短视频资产。"
            )
            self._send_json(
                {
                    "success": True,
                    "provider": "deepseek",
                    "model": "deepseek-v4-pro",
                    "title": title,
                    "summary": summary,
                    "sections": [
                        {"title": "市场空间", "content": "建议先聚焦高线城市体重管理需求。"},
                        {"title": "渠道策略", "content": "内容教育先行，再接私域承接和转化。"},
                        {"title": "演示链路", "content": "文案、音频和视频统一走可追踪资产 URL。"},
                    ],
                    "markdown": f"# {title}\n\n{summary}\n",
                }
            )
            return

        if parsed.path == "/api/v1/media/audio":
            base_url = self._base_url()
            self._send_json(
                {
                    "success": True,
                    "provider": "mimo",
                    "model": "local-voiceover-demo",
                    "voice": body.get("voice") or "default_zh",
                    "format": body.get("audio_format") or "mp3",
                    "audio_url": f"{base_url}/mock/audio/demo.mp3",
                    "audio_base64": load_audio_base64(),
                }
            )
            return

        if parsed.path == "/api/v1/media/video":
            prompt = body.get("prompt") or body.get("text") or "Medislim 视频脚本"
            base_url = self._base_url()
            self._send_json(
                {
                    "success": True,
                    "provider": "deepseek",
                    "model": "deepseek-v4-pro",
                    "audio_provider": "mimo",
                    "video_provider": "comfyui",
                    "video_model": "comfyui-local-demo",
                    "script": prompt,
                    "audio_url": f"{base_url}/mock/audio/demo.mp3",
                    "video_url": f"{base_url}/mock/video/demo.mp4",
                    "poster_url": f"{base_url}/mock/video/demo.jpg",
                    "voice": body.get("voice") or "default_zh",
                }
            )
            return

        self._send_json({"detail": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _base_url(self) -> str:
        host = self.headers.get("Host", "127.0.0.1:8788")
        return f"http://{host}"

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file_headers(self, path: Path, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tianyan local mock backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    print(f"Mock backend running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

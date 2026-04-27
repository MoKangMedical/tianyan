#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os

import httpx


async def run(base_url: str) -> None:
    api_key = os.environ.get("MIMO_API_KEY", "")
    if not api_key:
        raise SystemExit("MIMO_API_KEY is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tests = [
        (
            "models",
            "GET",
            "/models",
            None,
        ),
        (
            "audio",
            "POST",
            "/audio/speech",
            {
                "model": "mimo-v2-tts",
                "input": "欢迎来到天眼 Tianyan，这是一次真实联调。",
                "voice": "Chelsie",
                "response_format": "mp3",
            },
        ),
        (
            "video",
            "POST",
            "/videos/generations",
            {
                "model": "mimo-v2-video",
                "prompt": "A premium product teaser video for Tianyan, 6 seconds, blue and gold lighting.",
                "duration_seconds": 6,
                "size": "1280x720",
            },
        ),
        (
            "tts_chat",
            "POST",
            "/chat/completions",
            {
                "model": "mimo-v2-tts",
                "messages": [
                    {"role": "user", "content": "你好，请简单自我介绍。"}
                ],
                "max_tokens": 128,
            },
        ),
        (
            "tts_chat_audio",
            "POST",
            "/chat/completions",
            {
                "model": "mimo-v2-tts",
                "modalities": ["audio"],
                "audio": {
                    "voice": "default_zh",
                    "format": "mp3",
                },
                "messages": [
                    {
                        "role": "user",
                        "content": "请把 assistant 消息内容转成自然中文女声旁白。",
                    },
                    {
                        "role": "assistant",
                        "content": "欢迎来到天眼 Tianyan，这是一次真实联调。",
                    },
                ],
                "max_tokens": 16,
            },
        ),
        (
            "omni_chat",
            "POST",
            "/chat/completions",
            {
                "model": "mimo-v2-omni",
                "messages": [
                    {"role": "user", "content": "你好，请简单自我介绍。"}
                ],
                "max_tokens": 128,
            },
        ),
        (
            "video_model_check",
            "POST",
            "/chat/completions",
            {
                "model": "mimo-v2-video",
                "messages": [
                    {"role": "user", "content": "test"}
                ],
                "max_tokens": 16,
            },
        ),
    ]

    async with httpx.AsyncClient(timeout=90.0) as client:
        for name, method, path, payload in tests:
            print(f"=== {name} {method} {path} ===")
            try:
                response = await client.request(
                    method,
                    f"{base_url}{path}",
                    headers=headers,
                    json=payload,
                )
                print("status:", response.status_code)
                print("content-type:", response.headers.get("content-type", ""))
                if "application/json" in response.headers.get("content-type", ""):
                    try:
                        print(json.dumps(response.json(), ensure_ascii=False, indent=2)[:4000])
                    except Exception:
                        print(response.text[:4000])
                else:
                    print("bytes:", len(response.content))
            except Exception as exc:
                print("error:", type(exc).__name__, repr(exc))
                print("cause:", repr(getattr(exc, "__cause__", None)))
            print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://api.xiaomimimo.com/v1")
    args = parser.parse_args()
    asyncio.run(run(args.base_url))


if __name__ == "__main__":
    main()

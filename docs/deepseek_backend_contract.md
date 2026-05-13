# DeepSeek 后端接入契约

适用范围：当前微信小程序前端  
目标：把 Tianyan 的文本能力统一切到 `DeepSeek V4 Pro`，同时保留音频仍走 `Xiaomi Mimo`

## 1. 环境变量

后端至少应支持：

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=***
DEEPSEEK_MODEL=deepseek-v4-pro
MIMO_API_KEY=***
```

不要把任何密钥写进仓库。

如果视频链路要接 `ComfyUI`，后端还应支持：

```bash
VIDEO_PROVIDER=comfyui
COMFYUI_BASE_URL=https://comfyui.yourdomain.com
COMFYUI_WORKFLOW_ID=narrated-brief
```

## 2. 健康检查返回格式

小程序已经按下面这个格式兼容：

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm": {
    "provider": "deepseek",
    "model": "deepseek-v4-pro",
    "configured": true,
    "available": true
  },
  "media": {
    "audio": {
      "provider": "mimo",
      "model": "mimo-v2-tts",
      "configured": true,
      "available": true
    },
    "video": {
      "provider": "comfyui",
      "model": "comfyui-video",
      "configured": true,
      "available": true
    }
  }
}
```

## 3. 报告生成接口

建议保持：

- `POST /api/v1/report/generate`

建议请求体：

```json
{
  "product_name": "Medislim",
  "market": "China",
  "objective": "launch",
  "materials": [
    "市场研究摘要",
    "竞品价格带",
    "渠道假设"
  ]
}
```

建议响应体：

```json
{
  "success": true,
  "provider": "deepseek",
  "model": "deepseek-v4-pro",
  "title": "Medislim 中国上市建议",
  "summary": "......",
  "sections": [
    {
      "title": "市场空间",
      "content": "......"
    }
  ],
  "markdown": "# Medislim 中国上市建议\\n..."
}
```

## 4. 音频接口

保留：

- `POST /api/v1/media/audio`

这个接口不迁到 DeepSeek，继续由 `Xiaomi Mimo` 实现。

建议响应体：

```json
{
  "success": true,
  "provider": "mimo",
  "model": "mimo-v2-tts",
  "voice": "default_zh",
  "format": "mp3",
  "audio_url": "https://cdn.yourdomain.com/audio/abc.mp3",
  "audio_base64": "..."
}
```

## 5. 视频接口

建议保持：

- `POST /api/v1/media/video`

建议请求体：

```json
{
  "prompt": "为 Medislim 生成一个 20 秒产品上市旁白视频",
  "voice": "default_zh",
  "audio_format": "mp3",
  "video_provider": "comfyui",
  "video_mode": "narrated-brief"
}
```

建议响应体：

```json
{
  "success": true,
  "provider": "deepseek",
  "model": "deepseek-v4-pro",
  "audio_provider": "mimo",
  "video_provider": "comfyui",
  "video_model": "comfyui-video",
  "script": "......",
  "audio_url": "https://cdn.yourdomain.com/audio/abc.mp3",
  "video_url": "https://cdn.yourdomain.com/video/xyz.mp4",
  "poster_url": "https://cdn.yourdomain.com/video/xyz.jpg",
  "voice": "default_zh"
}
```

页面端现在会直接读取并展示：

- `audio_url`
- `video_url`
- `poster_url`

## 6. 当前前端状态

小程序已经完成这些准备：

- 首页展示文本模型和音频模型分工
- 健康检查会优先读取 `llm.model`
- 报告接口调用函数已经预留
- 案例页明确区分文本研究、音频旁白和 ComfyUI 视频
- 视频接口调用函数已经预留
- 页面会展示返回的音频和视频 URL

所以后端只要按这份契约实现，前端就不需要再大改。

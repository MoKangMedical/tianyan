# 微信小程序开始准备

## 已完成的第一步

仓库里已经新增一个可直接导入微信开发者工具的初始小程序骨架：

- `miniprogram/`

当前包含：

- 首页
  - API 地址配置
  - 健康探测
  - 能力映射
- 案例页
  - Medislim 样板展示
  - Narration Studio
  - 音频旁白生成
- 公共工具
  - API Base 持久化
  - `GET /api/health`
  - `POST /api/v1/media/audio`
  - `POST /api/v1/media/video`
  - `POST /api/v1/report/generate` 接口契约已预留

## 模型策略

当前准备方案已经统一成：

- 文本研究、分析、报告生成：`DeepSeek V4 Pro`
- 音频旁白：`Xiaomi Mimo`
- 视频生成：`ComfyUI`

原因很简单：

- DeepSeek 适合承接文本类 API
- 你当前要保留的旁白能力仍然需要音频供应商
- 视频生成需要单独的视频工作流
- 所以不能把音频和视频都硬切到 DeepSeek

## 当前默认后端

默认 API 地址：

- `https://tianyan-api.mokangmedical-dev.workers.dev`

它目前适合：

- 健康探测
- 音频生成
- 页面端展示视频 URL

它目前不适合：

- DeepSeek 全量报告生成
- 项目数据持久化
- 用户体系
- 真实 ComfyUI 生成链联调

## 你现在要做的事

### 1. 打开小程序骨架

用微信开发者工具导入：

- `miniprogram/`

### 1.1 本地演示模式

如果你现在没有正式后端，可以直接跑本地 mock：

```bash
python3 mock_backend/server.py
```

然后在微信开发者工具里，把小程序首页的 `API Base` 改成：

```text
http://127.0.0.1:8788
```

这时页面可以演示：

- `GET /api/health`
- `POST /api/v1/media/audio`
- `POST /api/v1/media/video`

并且会返回真实可访问的：

- `audio_url`
- `video_url`
- `poster_url`

### 2. 准备正式后端域名

如果要继续做成正式产品，需要一个可被微信小程序访问的 HTTPS 域名，例如：

- `https://api.yourdomain.com`

这个域名后面要在微信公众平台配置为：

- request 合法域名

### 3. 下一阶段建议

从工程顺序看，后面应该按这个顺序推进：

1. 把 Tianyan 后端部署到正式 HTTPS 域名
2. 后端文本模型固定到 `deepseek-v4-pro`
3. 把小程序默认 API Base 切到正式域名
4. 接入项目保存和历史记录
5. 接入微信登录

## 推荐的下一次开发目标

最合理的第二步不是先堆更多页面，而是补两项基础能力：

1. 正式后端域名
2. 小程序项目留存接口

没有这两项，小程序只能做演示，不能做真实业务闭环。

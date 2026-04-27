# 腾讯云落地清单

适用对象：当前 `天眼 Tianyan` 仓库  
当前形态：`GitHub Pages` 静态前端 + `FastAPI` 后端 + `Xiaomi Mimo` 音频能力 + 本地 `SQLite` 持久化

## 1. 目标架构

- 前端：继续保留 `GitHub Pages`
- 后端：部署到腾讯云 Linux 服务器
- 数据库：`TencentDB for PostgreSQL`
- 对象存储：`COS`
- 域名与 HTTPS：腾讯云域名解析 + SSL 证书

建议架构：

```text
GitHub Pages
  -> api.yourdomain.com
       -> Nginx / Caddy
            -> Tianyan FastAPI container
            -> TencentDB for PostgreSQL
            -> COS
            -> Xiaomi Mimo API
```

## 2. 资源采购清单

### 必买

- 1 台腾讯云服务器
  - 短期可用：轻量应用服务器
  - 正式商用建议：CVM
  - 建议起步规格：`2C4G`
  - 如果并发、报告生成和音频任务会上量，建议直接 `4C8G`
- 1 个 `TencentDB for PostgreSQL`
  - 同地域部署
  - 起步版本建议：PostgreSQL 14 或 15
  - 起步存储：`50GB` 起
- 1 个 `COS` 存储桶
  - 用于音频文件、报告导出文件、上传材料
- 1 个 API 域名
  - 例如：`api.xxx.com`
- 1 张 SSL 证书
  - 绑定 `api.xxx.com`

### 可选但建议

- `Cloud Monitor` 告警
- `CLS` 日志服务
- `Redis`
  - 后续做任务队列、缓存、限流计数时再上

## 3. 网络方案

### 你现在就能落地的方案

- 保留现有轻量服务器
- 后端跑在轻量服务器上
- 数据库先开公网访问
- 数据库白名单只放：
  - 服务器公网 IP
  - 管理员固定出口 IP

这个方案能最快上线，但不适合长期生产。

### 正式生产建议

- 后端迁到 `CVM`
- `CVM` 与 `TencentDB for PostgreSQL` 放在同地域、同 VPC
- 数据库只开私网访问
- 公网入口只暴露 `80/443`
- 应用容器内部口 `8000` 不直接暴露公网

### 如果继续使用轻量服务器

- 需要确认是否通过 `CCN` 打通与云数据库的私网访问
- 如果不做 `CCN`，那数据库只能走公网白名单方案

## 4. 仓库当前必须处理的配置差异

### 4.1 持久化路径不一致

当前代码默认 SQLite 路径：

- `tianyan/persistence.py` -> `/root/tianyan/data/tianyan.db`

当前 Docker 挂载路径：

- `docker-compose.yml` -> `./data:/app/data`

这两个路径不一致。结果是：

- 容器里 SQLite 可能不会落到你挂载的卷上
- 重建容器后数据可能丢失

上线前至少要做一件事：

- 方案 A：把 SQLite 路径改成 `/app/data/tianyan.db`
- 方案 B：把卷改成挂到 `/root/tianyan/data`

正式环境更建议直接迁移到 PostgreSQL，不再依赖 SQLite。

### 4.2 CORS 需要收紧

当前 `demo_server.py` 里是全开放：

- `allow_origins=["*"]`

正式上线建议只允许：

- `https://mokangmedical.github.io`
- 未来自定义官网域名
- 内部调试地址

## 5. 部署清单

### 5.1 服务器初始化

- 安装 Docker
- 安装 Docker Compose 插件
- 创建部署目录，例如 `/srv/tianyan`
- 创建专用运行用户
- 配置时区、NTP、基础防火墙
- 只放通：
  - `22`
  - `80`
  - `443`

### 5.2 代码与镜像

- 拉取仓库或上传发布包
- 构建镜像
- 不直接暴露 `8000`
- 用 Nginx 或 Caddy 反代到容器内部 `8000`

建议目录：

```text
/srv/tianyan/
  .env
  docker-compose.yml
  nginx/
  data/
  logs/
```

### 5.3 环境变量

至少准备这些：

```bash
APP_ENV=production
APP_VERSION=1.0.0
MIMO_API_KEY=***
DATABASE_URL=postgresql://tianyan_app:***@<db-host>:5432/tianyan
ALLOWED_ORIGINS=https://mokangmedical.github.io,https://yourdomain.com
COS_REGION=ap-guangzhou
COS_BUCKET=tianyan-prod-<appid>
COS_SECRET_ID=***
COS_SECRET_KEY=***
COS_PUBLIC_BASE_URL=https://<bucket>.cos.<region>.myqcloud.com
```

如果短期仍保留 SQLite 作为过渡：

```bash
PERSISTENCE_DB_PATH=/app/data/tianyan.db
```

## 6. 数据库清单

### 6.1 数据库选择

- 选 `TencentDB for PostgreSQL`
- 数据库名：`tianyan`
- 应用账号：`tianyan_app`
- 管理账号单独保留，不给应用直连使用

### 6.2 第一批表

基于当前仓库，至少要落这几类：

- `simulation_runs`
- `prediction_results`
- `audit_logs`
- `data_source_cache`
- `projects`
- `project_materials`
- `generated_reports`
- `generated_media`

前四类是当前 SQLite 已经有的结构，后四类是正式产品必须补的业务表。

### 6.3 备份策略

- 开启自动备份
- 保留最近 `7-14` 天
- 每周做一次手工恢复演练
- 生产前至少验证一次从备份恢复到测试实例

## 7. COS 清单

建议一个桶内分前缀管理：

```text
materials/
reports/
audio/
exports/
tmp/
```

建议规则：

- 原始上传材料放 `materials/`
- 生成后的音频放 `audio/`
- 导出 PDF / PPT / Markdown 放 `exports/`
- 数据库只存：
  - 文件 key
  - URL
  - MIME type
  - size
  - checksum

不要把大文件直接塞数据库。

### 7.1 COS 跨域

如果浏览器要直接访问 COS 文件，需要给桶配置 CORS，至少允许：

- `GET`
- `HEAD`
- `OPTIONS`

来源域名只放：

- `https://mokangmedical.github.io`
- 自定义官网域名

## 8. 域名与 HTTPS

- API 域名建议单独拆出来：`api.xxx.com`
- 服务器或负载均衡上绑定 SSL 证书
- 强制 HTTPS
- HTTP 301 跳转到 HTTPS

如果先不接负载均衡，单机 Nginx 就够用。

## 9. 安全清单

- 数据库不要长期对全网开放
- 安全组只放必要端口
- 应用口 `8000` 不直接暴露公网
- `MIMO_API_KEY`、数据库密码、COS 密钥只放环境变量
- 禁止把密钥写进仓库
- 收紧 CORS 白名单
- 接口层增加：
  - API key 或 JWT
  - 请求日志
  - 速率限制
- 管理后台与客户接口分开

## 10. 运维清单

- CPU、内存、磁盘、带宽做监控告警
- 进程异常自动拉起
- 磁盘使用率超过 `80%` 告警
- 数据库连接数、慢查询、存储使用率做监控
- 应用日志按天滚动
- 关键接口：
  - `/api/health`
  - `/api/v1/media/audio`
  - `/api/v1/report/generate`
  做可用性巡检

## 11. 上线顺序

### Phase 1：最快上线

1. 申请 `TencentDB for PostgreSQL`
2. 申请 `COS`
3. 服务器部署 Docker 版 Tianyan
4. 配置 `api.xxx.com`
5. 配置 HTTPS
6. 页面默认 API 地址改到新域名
7. 验证：
   - 首页可打开
   - 案例页可打开
   - `/api/health` 正常
   - 音频生成正常

### Phase 2：从 Demo 变成可交付产品

1. 持久化从 SQLite 迁到 PostgreSQL
2. 报告、音频、材料迁到 COS
3. 增加客户项目表和报告版本表
4. 接入登录和权限
5. 增加备份与监控

### Phase 3：正式商用

1. 后端迁到 CVM 同 VPC
2. 数据库改私网访问
3. 加 WAF / 网关 / 更严格限流
4. 灰度发布和回滚策略
5. 审计与数据保留策略

## 12. 你现在应该先买什么

如果目标是本周内上线一个能给客户演示的版本，先买这三样：

- `TencentDB for PostgreSQL`
- `COS`
- `api` 域名对应的 SSL

服务器你们已经有轻量实例，可以先复用。

## 13. 下一步建议

按优先级：

1. 先把数据库和 COS 申请下来
2. 我来把 Tianyan 改成真正支持 `DATABASE_URL` 和 COS 上传
3. 再把 GitHub Pages 的默认 API 地址切到你的正式域名

## 14. 官方文档

- TencentDB for PostgreSQL 产品页  
  https://www.tencentcloud.com/products/postgres
- TencentDB for PostgreSQL 功能说明  
  https://www.tencentcloud.com/document/product/409/4991
- TencentDB for PostgreSQL 网络配置  
  https://www.tencentcloud.com/document/product/409/44360
- Lighthouse 介绍  
  https://www.tencentcloud.com/document/product/1103/48118
- Lighthouse 与其他腾讯云资源私网互通 FAQ  
  https://www.tencentcloud.com/pt/document/product/1103/41257
- Lighthouse 私网互联与 CCN  
  https://www.tencentcloud.com/document/product/236/58083
- COS Getting Started  
  https://www.tencentcloud.com/document/product/436/10199
- COS CORS 配置  
  https://www.tencentcloud.com/ind/document/product/436/13318
- SSL Certificate Service  
  https://www.tencentcloud.com/products/ssl

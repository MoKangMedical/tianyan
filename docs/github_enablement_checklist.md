# GitHub 启用清单

适用仓库：

- `MoKangMedical/tianyan`

目标：

- 把当前仓库从“只放代码”升级到“可协作、可审计、可上线”

## 1. 立刻完成

### 1.1 旋转旧 token

当前本地 remote 已经去掉了带凭证 URL，但旧 token 仍应视为泄露。

立即在 GitHub:

1. 进入 `Settings`
2. 进入 `Developer settings`
3. 进入 `Personal access tokens`
4. 撤销旧 token
5. 如确有需要，创建新 token，最小化 scope

### 1.2 启用 Secret Scanning

进入：

- `Settings -> Security -> Code security and analysis`

开启：

- `Secret scanning`
- `Push protection`

## 2. CI

仓库里已经新增：

- `.github/workflows/ci.yml`

它会自动执行：

- Python 依赖安装
- `py_compile`
- 小程序 JS 语法检查
- `pytest -q`

你现在只需要把改动推到 GitHub，Actions 就会开始工作。

## 3. Branch Protection / Ruleset

推荐直接对 `main` 建规则：

1. 进入 `Settings -> Rules -> Rulesets`
2. 新建一个作用于默认分支 `main` 的 ruleset
3. 开启这些规则：
   - Require a pull request before merging
   - Require status checks to pass
   - Block force pushes
   - Block deletions

推荐把必须通过的状态检查至少设成：

- `test`

## 4. Environments

进入：

- `Settings -> Environments`

建议至少建两个环境：

- `staging`
- `production`

### 4.1 建议的 secrets

- `DEEPSEEK_API_KEY`
- `MIMO_API_KEY`
- `COMFYUI_BASE_URL`
- `PUBLIC_BASE_URL`

### 4.2 建议的 vars

- `DEEPSEEK_MODEL=deepseek-v4-pro`
- `MIMO_AUDIO_MODEL=local-voiceover-demo`
- `COMFYUI_VIDEO_MODEL=comfyui-local-demo`

## 5. Projects

进入：

- `Projects`

建议至少建一个：

- `Tianyan Delivery`

建议字段：

- `Status`
- `Priority`
- `Area`
- `Target`

建议 `Area` 取值：

- `Backend`
- `Mini Program`
- `Media Pipeline`
- `Deployment`
- `Customer Delivery`

## 6. Discussions

如果这个仓库需要沉淀方案和外部协作反馈，建议开启：

- `Settings -> General -> Features -> Discussions`

适合放：

- 产品规划
- 使用问答
- Demo 反馈
- 行业模板征集

## 7. 建议的 GitHub 使用顺序

按优先级：

1. Secret scanning / push protection
2. CI workflow
3. Ruleset
4. Environments
5. Projects
6. Discussions

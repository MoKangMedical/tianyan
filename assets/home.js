const endpointCatalog = [
  {
    tag: "core",
    method: "GET",
    path: "/api/health",
    label: "健康检查",
    description: "用于确认服务是否存活，以及当前实例的版本和时间戳。",
    useCase: "给前端首页、运维探针和 GitHub Pages 文档页提供最基础的在线状态校验。",
    returns: "status, service, version, timestamp",
    request: "curl http://localhost:8000/api/health",
    response: `{
  "status": "healthy",
  "service": "tianyan",
  "version": "1.0.0",
  "timestamp": 1775830837.611371
}`
  },
  {
    tag: "population",
    method: "POST",
    path: "/api/population",
    label: "创建合成人群",
    description: "按年龄、地域、性别和样本量生成用于仿真的合成人群。",
    useCase: "在做新品上市、价格测试和渠道模拟前，先明确要模拟哪一群人。",
    returns: "population_summary, sample_profiles",
    request: `curl -X POST http://localhost:8000/api/population \\
  -H "Content-Type: application/json" \\
  -d '{
    "size": 3000,
    "region": "一线城市",
    "age_min": 25,
    "age_max": 45,
    "gender": "female",
    "seed": 42
  }'`,
    response: `{
  "success": true,
  "population_size": 3000,
  "summary": {
    "region": "一线城市",
    "age_range": [25, 45],
    "gender": "female"
  }
}`
  },
  {
    tag: "simulation",
    method: "POST",
    path: "/api/simulate",
    label: "通用仿真",
    description: "对任意商业场景进行基础人群仿真。",
    useCase: "在没有预置模板的情况下，快速验证一个新业务问题是否值得深挖。",
    returns: "scenario_result, metrics, recommendations",
    request: `curl -X POST http://localhost:8000/api/simulate \\
  -H "Content-Type: application/json" \\
  -d '{
    "scenario_description": "一款299元减重产品在上海投放",
    "population_size": 500,
    "rounds": 2
  }'`,
    response: `{
  "success": true,
  "scenario": "一款299元减重产品在上海投放",
  "metrics": {
    "purchase_intent": 0.61,
    "price_sensitivity": 0.54
  }
}`
  },
  {
    tag: "china",
    method: "POST",
    path: "/api/kol",
    label: "KOL 效果预测",
    description: "比较不同 KOL 类型的触达、互动、转化和 ROI。",
    useCase: "先决定该投头部、美妆、中腰部健康还是素人种草号。",
    returns: "reach, engagement, conversion, roi",
    request: `curl -X POST http://localhost:8000/api/kol \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_name": "纤姿GLP-1减重胶囊",
    "product_price": 299,
    "kol_type": "素人种草号",
    "population_size": 1000
  }'`,
    response: `{
  "success": true,
  "kol_type": "素人种草号",
  "prediction": {
    "reach": 2160000,
    "engagement": 0.12,
    "conversion": 0.081,
    "roi": 5232.6
  }
}`
  },
  {
    tag: "china",
    method: "POST",
    path: "/api/livestream",
    label: "直播带货预测",
    description: "对不同直播平台的观看规模、转化和 GMV 进行测算。",
    useCase: "决定首场直播应该放在小红书、抖音还是快手，以及用什么折扣率。",
    returns: "viewers, conversion, gmv, best_time",
    request: `curl -X POST http://localhost:8000/api/livestream \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_name": "纤姿GLP-1减重胶囊",
    "product_price": 299,
    "platform": "小红书",
    "discount_rate": 0.2
  }'`,
    response: `{
  "success": true,
  "platform": "小红书",
  "prediction": {
    "viewers": 150000,
    "conversion": 0.08,
    "gmv": 3049800,
    "best_time": "20:00-22:00"
  }
}`
  },
  {
    tag: "china",
    method: "POST",
    path: "/api/channel",
    label: "电商渠道优化",
    description: "对淘宝、京东、拼多多、抖音电商等平台进行匹配度打分。",
    useCase: "不是所有渠道都要同步上线，先看最值得投放的前两名。",
    returns: "channel_ranking, channel_score, recommendation",
    request: `curl -X POST http://localhost:8000/api/channel \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_name": "纤姿GLP-1减重胶囊",
    "product_price": 299,
    "product_category": "健康消费品"
  }'`,
    response: `{
  "success": true,
  "ranking": [
    {"platform": "小红书", "score": 1.009},
    {"platform": "淘宝", "score": 0.866},
    {"platform": "抖音电商", "score": 0.808}
  ]
}`
  },
  {
    tag: "china",
    method: "POST",
    path: "/api/seeding",
    label: "小红书种草预测",
    description: "比较测评视频、开箱体验、种草笔记、教程攻略等内容风格的表现。",
    useCase: "决定内容团队第一批该产哪类素材，而不是凭感觉选风格。",
    returns: "impressions, interactions, rate, best_style",
    request: `curl -X POST http://localhost:8000/api/seeding \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_name": "纤姿GLP-1减重胶囊",
    "product_price": 299,
    "content_style": "测评视频",
    "num_notes": 100
  }'`,
    response: `{
  "success": true,
  "content_style": "测评视频",
  "prediction": {
    "impressions": 194400,
    "interactions": 11433,
    "rate": 0.0588
  }
}`
  },
  {
    tag: "advanced",
    method: "POST",
    path: "/api/v1/predict/full",
    label: "完整预测",
    description: "把产品、人群、KOL、直播、种草和渠道一次性串起来。",
    useCase: "适合业务负责人做首轮 go/no-go 判断，不必手工串多个接口。",
    returns: "full_funnel_result, recommendation, summary",
    request: `curl -X POST http://localhost:8000/api/v1/predict/full \\
  -H "Content-Type: application/json" \\
  -d '{"product_name":"GLP-1减重针","product_price":399}'`,
    response: `{
  "success": true,
  "summary": {
    "purchase_intent": 0.62,
    "best_channel": "小红书",
    "best_kol_type": "素人种草号"
  }
}`
  },
  {
    tag: "advanced",
    method: "POST",
    path: "/api/v1/report/generate",
    label: "生成报告",
    description: "输出结构化商业报告，覆盖结论、分群洞察、渠道建议与执行动作。",
    useCase: "把分析结果转成客户可读材料，不再手工整报告。",
    returns: "markdown_report, json_report, recommendations",
    request: `curl -X POST http://localhost:8000/api/v1/report/generate \\
  -H "Content-Type: application/json" \\
  -d '{"product_name":"GLP-1减重针","product_price":399}'`,
    response: `{
  "success": true,
  "report_type": "McKinsey",
  "sections": ["Executive Summary", "Market", "Channels", "Risks"]
}`
  },
  {
    tag: "advanced",
    method: "GET",
    path: "/api/v1/templates",
    label: "获取模板清单",
    description: "返回所有预置行业模板的 key、名称、行业和描述。",
    useCase: "在页面端做模板浏览器或初始化下拉选择框。",
    returns: "count, templates[]",
    request: "curl http://localhost:8000/api/v1/templates",
    response: `{
  "success": true,
  "count": 5,
  "templates": [
    {"key": "glp1_weight_loss", "name": "GLP-1减重产品上市"},
    {"key": "telehealth_platform", "name": "远程医疗平台"}
  ]
}`
  },
  {
    tag: "advanced",
    method: "POST",
    path: "/api/v1/template/run",
    label: "运行行业模板",
    description: "在预置模板参数上直接执行一次完整预测。",
    useCase: "让业务方从模板起步，而不是从零填写大量参数。",
    returns: "template, industry, prediction, competitor_hints",
    request: `curl -X POST http://localhost:8000/api/v1/template/run \\
  -H "Content-Type: application/json" \\
  -d '{
    "template_key":"glp1_weight_loss",
    "product_name":"SlimGuard",
    "product_price":399
  }'`,
    response: `{
  "success": true,
  "template": "GLP-1减重产品上市",
  "industry": "消费医疗",
  "prediction": {
    "key_metrics": {
      "purchase_intent": 0.63,
      "best_channel": "小红书"
    }
  }
}`
  },
  {
    tag: "advanced",
    method: "GET",
    path: "/api/v1/dashboard",
    label: "平台仪表盘",
    description: "返回版本、产品矩阵、模板数量和接口数量等高层摘要。",
    useCase: "给前端首页和运营面板快速渲染平台总览。",
    returns: "version, stats, products, industry_templates",
    request: "curl http://localhost:8000/api/v1/dashboard",
    response: `{
  "success": true,
  "platform": "天眼 Tianyan",
  "version": "1.0.0",
  "stats": {
    "industry_templates": 5,
    "ai_engine": "MIMO API",
    "total_endpoints": 16
  }
}`
  },
  {
    tag: "advanced",
    method: "POST",
    path: "/api/v1/compare",
    label: "双产品对比",
    description: "对两个候选产品的购买意愿和关键指标做并排比较。",
    useCase: "适合 SKU 取舍、不同定价包型 A/B 对比和投前筛选。",
    returns: "product_a, product_b, winner",
    request: `curl -X POST http://localhost:8000/api/v1/compare \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_a":"产品A",
    "product_b":"产品B",
    "price_a":299,
    "price_b":399
  }'`,
    response: `{
  "success": true,
  "winner": "产品A",
  "product_a": {"metrics": {"purchase_intent": 0.62}},
  "product_b": {"metrics": {"purchase_intent": 0.51}}
}`
  },
  {
    tag: "media",
    method: "POST",
    path: "/api/v1/media/audio",
    label: "音频生成",
    description: "通过 Xiaomi Mimo API 将文案直接合成为旁白或语音素材。",
    useCase: "给报告页、产品介绍视频、直播脚本和案例演示生成统一口径的音频素材。",
    returns: "audio_base64, content_type, voice, format",
    request: `curl -X POST http://localhost:8000/api/v1/media/audio \\
  -H "Content-Type: application/json" \\
  -d '{
    "text":"欢迎来到天眼 Tianyan",
    "voice":"default_zh",
    "audio_format":"mp3"
  }'`,
    response: `{
  "success": true,
  "content_type": "audio/mp3",
  "voice": "default_zh",
  "format": "mp3",
  "audio_base64": "<base64>"
}`
  },
  {
    tag: "media",
    method: "POST",
    path: "/api/v1/media/video",
    label: "视频生成",
    description: "保留 Xiaomi Mimo 视频能力入口，并在当前公开 API 未开放视频模型时明确返回未支持说明。",
    useCase: "避免前端或客户侧误以为视频已打通；一旦 Xiaomi 开放视频模型，这个入口可以直接升级为真实调用。",
    returns: "detail",
    request: `curl -X POST http://localhost:8000/api/v1/media/video \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt":"生成一个 10 秒产品展示视频",
    "duration_seconds":10,
    "size":"1280x720"
  }'`,
    response: `{
  "detail": "Xiaomi Mimo 当前公开 API 仅验证到文本与 TTS 模型。/videos/generations 为 404，且 /models 未返回视频模型。"
}`
  },
  {
    tag: "legacy",
    method: "GET",
    path: "/",
    label: "Landing Page",
    description: "服务端自带的首页入口，可直接在本地运行后访问。",
    useCase: "GitHub Pages 主站用于说明能力，本地 FastAPI 首页用于部署后直接展示。",
    returns: "HTML landing page",
    request: "open http://localhost:8000/",
    response: `<!DOCTYPE html>
<html lang="zh-CN">
  <head>...</head>
  <body>天眼 Tianyan Landing Page</body>
</html>`
  },
  {
    tag: "legacy",
    method: "GET",
    path: "/docs",
    label: "Swagger UI",
    description: "FastAPI 自动生成的文档入口，适合开发调试时直接试接口。",
    useCase: "GitHub Pages 负责叙事与案例；本地 Swagger 负责真实交互和调试。",
    returns: "Interactive OpenAPI UI",
    request: "open http://localhost:8000/docs",
    response: `Swagger UI
  - Try it out
  - Schemas
  - Response preview`
  }
];

const templates = [
  {
    key: "glp1_weight_loss",
    name: "GLP-1减重产品上市",
    industry: "消费医疗",
    description: "适合评估减重类新品的购买意愿、渠道偏好、复购与传播力。",
    highlights: ["299-599 定价带", "抖音/小红书/微信", "推荐女性 25-55 岁"]
  },
  {
    key: "health_supplement",
    name: "保健品上市",
    industry: "健康消费品",
    description: "适合营养补充剂、保健食品与功能性消费品。",
    highlights: ["98-298 定价带", "抖音/淘宝/京东", "全人群模板"]
  },
  {
    key: "skincare_launch",
    name: "护肤品上市",
    industry: "美妆护肤",
    description: "适合功能性护肤品、功效型美妆和内容电商推广。",
    highlights: ["18-45 岁女性", "小红书强相关", "种草转化重点"]
  },
  {
    key: "telehealth_platform",
    name: "远程医疗平台",
    industry: "数字健康",
    description: "适合评估注册转化、付费转化和互联网医疗平台产品策略。",
    highlights: ["0-99 客单价", "微信/抖音/应用商店", "推荐样本 8000"]
  },
  {
    key: "male_health",
    name: "男性健康管理",
    industry: "消费医疗",
    description: "适合关注隐私顾虑、支付意愿与渠道保密性的男性健康产品。",
    highlights: ["199-599 定价带", "抖音/微信/知乎", "男性 25-55 岁"]
  }
];

const defaultCapabilityDomains = [
  {
    kicker: "Policy and Governance",
    tag: "政策与治理",
    title: "政策、监管与治理环境研究",
    description: "聚焦政策文本、监管节奏、区域治理导向和对产业、企业、项目的影响，不做人事、选举或敏感事件预测。",
    questions: [
      "政策方向如何改变市场准入、支付环境和监管成本？",
      "地方执行力度会不会放大或削弱国家层面的政策意图？",
      "某项政策落地后，企业的收入、成本和组织动作会如何变化？"
    ],
    materials: [
      "政策文件、征求意见稿、监管通告、白皮书",
      "地方政府工作报告、园区招商资料、会议纪要",
      "行业协会文件、法规对比与执行细则"
    ],
    outputs: [
      "政策影响评估报告",
      "监管风险地图与情景树",
      "区域落地优先级建议"
    ],
    boundary: "只做政策与产业环境评估，不做敏感政治事件、人事变动或选举预测。"
  },
  {
    kicker: "Economy and Industry",
    tag: "经济与产业",
    title: "宏观经济、产业链与投资判断",
    description: "把宏观指标、产业结构、竞争格局和需求变化串成一个可落地的商业判断框架。",
    questions: [
      "这个赛道未来 12-36 个月的需求拐点在哪里？",
      "成本、价格、竞争和政策共同作用下，利润池会如何迁移？",
      "项目适合进入、扩张、等待还是退出？"
    ],
    materials: [
      "统计公报、行业报告、招股书、券商研报、财报电话会",
      "渠道数据、价格带数据、供应链访谈",
      "区域产业规划、投资公告与项目清单"
    ],
    outputs: [
      "行业趋势研判",
      "市场进入与竞争策略报告",
      "投资可行性与回收预期"
    ],
    boundary: "聚焦产业、市场和企业层面的经济判断，不做违法合规之外的内幕推断。"
  },
  {
    kicker: "Culture and Consumption",
    tag: "文化与消费",
    title: "文化叙事、舆论气候与消费心智",
    description: "把内容生态、社交传播、代际认同与品牌语义转成可执行的消费策略。",
    questions: [
      "目标人群为什么会认同、排斥或忽略一个品牌叙事？",
      "文化语境如何影响转化、信任和复购？",
      "什么样的内容与 KOL 组合最适合建立市场教育？"
    ],
    materials: [
      "舆情语料、社媒内容、用户评论、KOL 样本内容",
      "访谈纪要、焦点小组材料、品牌资产研究",
      "文化消费趋势、代际研究和内容平台规则"
    ],
    outputs: [
      "内容策略与叙事地图",
      "人群心智画像",
      "品牌进入与增长建议"
    ],
    boundary: "聚焦公开传播与文化消费趋势，不触碰个人隐私与敏感内容识别。"
  },
  {
    kicker: "National and Regional Development",
    tag: "国家发展",
    title: "国家发展、区域机会与长期布局",
    description: "用国家战略、区域发展路径、人口迁移和产业升级线索判断长期项目机会。",
    questions: [
      "某个项目更适合在哪个城市群、产业带或政策窗口落地？",
      "国家发展方向会如何改变人才、资本与需求分布？",
      "项目的中长期增长路径应该如何与国家发展议题对齐？"
    ],
    materials: [
      "五年规划、区域规划、专项行动方案、统计年鉴",
      "人口迁移、城市更新、基础设施与产业园区资料",
      "地方招商手册、项目申报文件与绩效目标"
    ],
    outputs: [
      "区域布局建议",
      "中长期机会地图",
      "项目路径与阶段里程碑"
    ],
    boundary: "聚焦公开战略、区域发展与产业政策，不做敏感国家安全或政治事件判断。"
  }
];

const defaultMaterialPipelines = [
  {
    kicker: "Policy Document",
    title: "政策文件 / 监管文本",
    description: "将政策语言拆成监管方向、适用范围、受益者、受损者和执行节奏，形成影响判断。",
    signals: [
      "监管强度、时间窗口、适用对象",
      "地方执行差异与配套资源",
      "行业门槛、价格机制、支付变化"
    ],
    analysis: [
      "政策语义切片与条款归因",
      "行业与区域映射",
      "情景推演与机会/风险权重排序"
    ],
    outlook: `未来预期
- 未来 6-12 个月政策将如何改变市场进入门槛
- 哪些玩家受益、哪些环节承压
- 项目节奏应提前、延后还是分阶段推进`,
    deliverable: `McKinsey-style material
1. Executive summary
2. Policy impact tree
3. Region-by-region implications
4. Risk dashboard
5. 100-day response plan`
  },
  {
    kicker: "Research Report",
    title: "行业研究 / 券商研报 / 白皮书",
    description: "将外部报告转为市场假设、需求弹性、竞争差异和项目的未来区间判断。",
    signals: [
      "市场规模、增长率、利润池迁移",
      "竞争者策略、价格带、技术代际",
      "需求驱动与供给约束"
    ],
    analysis: [
      "假设抽取与交叉验证",
      "竞争格局与增长逻辑重构",
      "项目收益区间与关键拐点判断"
    ],
    outlook: `未来预期
- 赛道未来 12-36 个月增长曲线
- 竞争格局是否会重排
- 项目进入后 3 个季度内最可能发生的变化`,
    deliverable: `McKinsey-style material
1. Market attractiveness memo
2. Scenario comparison
3. Revenue / margin outlook
4. Entry strategy recommendation
5. Appendix with source reconciliation`
  },
  {
    kicker: "Interview and Minutes",
    title: "访谈纪要 / 会议纪要 / 调研记录",
    description: "把分散的一手信息转成结构化洞察，明确哪些是事实、哪些是假设、哪些需要再验证。",
    signals: [
      "高频痛点与一线判断",
      "组织分歧、执行阻力、渠道反馈",
      "客户需求与购买障碍"
    ],
    analysis: [
      "观点聚类与冲突检测",
      "证据级别分层",
      "行动项与验证实验设计"
    ],
    outlook: `未来预期
- 这个项目最可能卡在哪个环节
- 一线反馈指向的是短期问题还是结构性问题
- 下一轮验证应该优先投哪里`,
    deliverable: `McKinsey-style material
1. Insight synthesis note
2. Hypothesis matrix
3. Decision memo
4. Validation roadmap
5. Interview evidence appendix`
  },
  {
    kicker: "Prospectus and Financials",
    title: "招股书 / 财报 / 商业计划书",
    description: "从公开财务与叙事中提炼项目的经营杠杆、增长约束与未来估值支撑逻辑。",
    signals: [
      "收入结构、毛利、现金流与 CAPEX",
      "增长驱动与风险披露",
      "组织能力、渠道能力和运营质量"
    ],
    analysis: [
      "经营结构拆解",
      "增长与盈利桥接",
      "市场叙事与现实兑现度比较"
    ],
    outlook: `未来预期
- 收入与利润的最可能区间
- 哪些变量决定估值与市场预期
- 未来 4-6 个季度的关键观察点`,
    deliverable: `McKinsey-style material
1. Financial quality review
2. Growth thesis assessment
3. Forward-looking KPI pack
4. Board-level risk notes
5. Strategy options`
  },
  {
    kicker: "Public Opinion and Media",
    title: "舆情 / 内容 / 媒体监测",
    description: "将品牌语义、平台情绪和热点结构与商业转化路径对应起来。",
    signals: [
      "情绪变化与主题聚类",
      "内容扩散结构与平台差异",
      "品牌信任、争议点和触发因素"
    ],
    analysis: [
      "舆论演化图谱",
      "平台与人群映射",
      "品牌动作优先级排序"
    ],
    outlook: `未来预期
- 舆情会自然回落还是继续放大
- 哪类内容最能修复信任或推动转化
- 品牌接下来 2-4 周应采取什么动作`,
    deliverable: `McKinsey-style material
1. Narrative map
2. Sentiment dashboard
3. Response playbook
4. Channel-specific content brief
5. Weekly monitoring template`
  }
];

const defaultDeliverables = [
  {
    title: "Executive Summary",
    description: "把项目的结论、判断和建议压缩进一页可读、可汇报的高层摘要。",
    bullets: ["一句话结论", "三条关键判断", "行动优先级", "董事会可读格式"]
  },
  {
    title: "Future Outlook Pack",
    description: "围绕未来 6-36 个月，把增长、风险、政策和竞争变量做成可复盘的预期材料。",
    bullets: ["乐观/基准/保守情景", "关键拐点", "预警指标", "季度更新机制"]
  },
  {
    title: "McKinsey-style Report",
    description: "结构化报告不是简单排版，而是完整的论点链、证据链和建议链。",
    bullets: ["Executive summary", "Market and policy analysis", "Scenario tree", "Implementation roadmap"]
  },
  {
    title: "Risk and Decision Memo",
    description: "帮助客户在进入、扩张、投资和合作前完成风险排序与决策闭环。",
    bullets: ["风险分层", "概率与影响评估", "缓释动作", "决策建议"]
  },
  {
    title: "Client-facing Deck",
    description: "把复杂研究转成客户团队、合作伙伴和投资方都能直接看的 презентация。",
    bullets: ["品牌化版式", "图表摘要", "关键数据附录", "讨论用章节结构"]
  },
  {
    title: "100-day Action Plan",
    description: "研究最终要落到执行，所以每个项目都应有可追踪的阶段计划。",
    bullets: ["阶段目标", "预算与资源", "KPI 追踪", "复盘节点"]
  }
];

let capabilityDomains = [];
let materialPipelines = [];
let deliverables = [];
let reportLibrary = [];
let skillLibrary = [];

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatMoney(value) {
  if (value >= 100000000) {
    return `¥${(value / 100000000).toFixed(2)}亿`;
  }
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(0)}万`;
  }
  return `¥${value}`;
}

function formatCompactNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

async function loadContentCatalogs() {
  const [
    domainResult,
    materialResult,
    deliverableResult,
    reportResult,
    skillResult
  ] = await Promise.allSettled([
    loadJson("content/research-domains.json"),
    loadJson("content/material-pipelines.json"),
    loadJson("content/deliverables.json"),
    loadJson("content/report-library.json"),
    loadJson("content/skill-library.json")
  ]);

  capabilityDomains = domainResult.status === "fulfilled"
    ? (domainResult.value.items || defaultCapabilityDomains)
    : defaultCapabilityDomains;
  materialPipelines = materialResult.status === "fulfilled"
    ? (materialResult.value.items || defaultMaterialPipelines)
    : defaultMaterialPipelines;
  deliverables = deliverableResult.status === "fulfilled"
    ? (deliverableResult.value.items || defaultDeliverables)
    : defaultDeliverables;
  reportLibrary = reportResult.status === "fulfilled"
    ? (reportResult.value.items || [])
    : [];
  skillLibrary = skillResult.status === "fulfilled"
    ? (skillResult.value.items || [])
    : [];

  [domainResult, materialResult, deliverableResult, reportResult, skillResult]
    .filter((result) => result.status === "rejected")
    .forEach((result) => console.error("Failed to load content catalog", result.reason));
}

function buildViewerLink(path, mode, metadata = {}) {
  const params = new URLSearchParams({
    path,
    mode,
    ...Object.fromEntries(
      Object.entries(metadata).filter(([, value]) => value)
    )
  });
  return `library/viewer.html?${params.toString()}`;
}

function buildContentHref(path, mode, metadata = {}) {
  if (!path) {
    return "#";
  }

  if (/\.html?$/i.test(path)) {
    return path;
  }

  return buildViewerLink(path, mode, metadata);
}

function renderEndpointMenu() {
  const list = document.getElementById("endpoint-list");
  list.innerHTML = endpointCatalog.map((endpoint, index) => `
    <button class="endpoint-item" type="button" data-endpoint-index="${index}" aria-selected="${index === 0 ? "true" : "false"}">
      <span>${endpoint.method} · ${endpoint.tag}</span>
      <strong>${endpoint.label}</strong>
      <small>${endpoint.path}</small>
    </button>
  `).join("");
}

function renderEndpoint(index) {
  const endpoint = endpointCatalog[index];
  document.querySelectorAll("[data-endpoint-index]").forEach((button, buttonIndex) => {
    button.setAttribute("aria-selected", String(buttonIndex === index));
  });
  document.getElementById("endpoint-method").textContent = endpoint.method;
  document.getElementById("endpoint-tag").textContent = endpoint.tag;
  document.getElementById("endpoint-path").textContent = endpoint.path;
  document.getElementById("endpoint-description").textContent = endpoint.description;
  document.getElementById("endpoint-use-case").textContent = endpoint.useCase;
  document.getElementById("endpoint-returns").textContent = endpoint.returns;
  document.getElementById("endpoint-request").textContent = endpoint.request;
  document.getElementById("endpoint-response").textContent = endpoint.response;

  const copyRequestButton = document.getElementById("copy-request-button");
  const copyJsonButton = document.getElementById("copy-json-button");
  copyRequestButton.onclick = async () => copyText(endpoint.request, copyRequestButton);
  copyJsonButton.onclick = async () => copyText(endpoint.response, copyJsonButton);
}

async function copyText(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const previous = button.textContent;
    button.textContent = "已复制";
    window.setTimeout(() => {
      button.textContent = previous;
    }, 1200);
  } catch {
    button.textContent = "复制失败";
  }
}

function renderTemplates() {
  const grid = document.getElementById("template-grid");
  grid.innerHTML = templates.map((template) => `
    <article class="template-card">
      <span class="panel-label">${template.industry}</span>
      <h3>${template.name}</h3>
      <p>${template.description}</p>
      <div class="template-meta">
        <span>${template.key}</span>
        ${template.highlights.map((item) => `<span>${item}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

function renderBulletStack(targetId, items) {
  document.getElementById(targetId).innerHTML = items.map((item) => `<span>${item}</span>`).join("");
}

function renderDomainMenu() {
  const list = document.getElementById("domain-list");
  list.innerHTML = capabilityDomains.map((domain, index) => `
    <button class="endpoint-item" type="button" data-domain-index="${index}" aria-selected="${index === 0 ? "true" : "false"}">
      <span>${domain.tag}</span>
      <strong>${domain.title}</strong>
      <small>${domain.description}</small>
    </button>
  `).join("");
}

function renderDomain(index) {
  const domain = capabilityDomains[index];
  document.querySelectorAll("[data-domain-index]").forEach((button, buttonIndex) => {
    button.setAttribute("aria-selected", String(buttonIndex === index));
  });
  document.getElementById("domain-kicker").textContent = domain.kicker;
  document.getElementById("domain-boundary-tag").textContent = domain.tag;
  document.getElementById("domain-title").textContent = domain.title;
  document.getElementById("domain-description").textContent = domain.description;
  renderBulletStack("domain-questions", domain.questions);
  renderBulletStack("domain-materials", domain.materials);
  renderBulletStack("domain-outputs", domain.outputs);
  document.getElementById("domain-boundary").textContent = domain.boundary;
}

function renderMaterialMenu() {
  const list = document.getElementById("material-list");
  list.innerHTML = materialPipelines.map((material, index) => `
    <button class="endpoint-item" type="button" data-material-index="${index}" aria-selected="${index === 0 ? "true" : "false"}">
      <span>${material.kicker}</span>
      <strong>${material.title}</strong>
      <small>${material.description}</small>
    </button>
  `).join("");
}

function renderMaterial(index) {
  const material = materialPipelines[index];
  document.querySelectorAll("[data-material-index]").forEach((button, buttonIndex) => {
    button.setAttribute("aria-selected", String(buttonIndex === index));
  });
  document.getElementById("material-kicker").textContent = material.kicker;
  document.getElementById("material-title").textContent = material.title;
  document.getElementById("material-description").textContent = material.description;
  renderBulletStack("material-signals", material.signals);
  renderBulletStack("material-analysis", material.analysis);
  document.getElementById("material-outlook").textContent = material.outlook;
  document.getElementById("material-deliverable").textContent = material.deliverable;

  const copyButton = document.getElementById("copy-deliverable-button");
  copyButton.onclick = async () => copyText(material.deliverable, copyButton);
}

function renderDeliverables() {
  const grid = document.getElementById("deliverable-grid");
  grid.innerHTML = deliverables.map((item) => `
    <article class="deliverable-card">
      <span class="panel-label">Client Deliverable</span>
      <h3>${item.title}</h3>
      <p>${item.description}</p>
      <ul>
        ${item.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}
      </ul>
    </article>
  `).join("");
}

function renderReportLibrary() {
  const count = document.getElementById("report-library-count");
  const grid = document.getElementById("report-library-grid");
  count.textContent = `${reportLibrary.length} reports`;
  grid.innerHTML = reportLibrary.map((item) => `
    <article class="library-card">
      <span class="panel-label">${item.category}</span>
      <strong>${item.title}</strong>
      <small>${item.summary}</small>
      <span>${item.deliverable}</span>
      <div class="library-links">
        <a href="${buildContentHref(item.path, "report", {
          title: item.title,
          category: item.category,
          summary: item.summary,
          meta: item.deliverable
        })}">浏览详情</a>
        ${item.secondaryPath ? `<a href="${buildContentHref(item.secondaryPath, "report", {
          title: `${item.title} · 附件`,
          category: item.category,
          summary: item.summary,
          meta: item.secondaryLabel || "补充材料"
        })}">${item.secondaryLabel || "附加材料"}</a>` : ""}
        ${item.casePath ? `<a href="${item.casePath}">查看案例</a>` : ""}
      </div>
    </article>
  `).join("");
}

function renderSkillLibrary() {
  const count = document.getElementById("skill-library-count");
  const grid = document.getElementById("skill-library-grid");
  count.textContent = `${skillLibrary.length} skills`;
  grid.innerHTML = skillLibrary.map((item) => `
    <article class="library-card">
      <span class="panel-label">${item.category}</span>
      <strong>${item.displayName}</strong>
      <small>${item.summary}</small>
      <span>触发：${item.triggers.join(" / ")}</span>
      <div class="library-links">
        <a href="${buildContentHref(item.skillPath, "skill", {
          title: item.displayName,
          category: item.category,
          summary: item.summary,
          meta: `触发：${item.triggers.join(" / ")}`
        })}">打开 Skill</a>
        <a href="${buildContentHref(item.sourcePath, "source", {
          title: `${item.displayName} · 源材料`,
          category: item.category,
          summary: item.summary,
          meta: item.sourceLabel || "源报告"
        })}">${item.sourceLabel || "源报告"}</a>
        ${item.secondaryPath ? `<a href="${buildContentHref(item.secondaryPath, "source", {
          title: `${item.displayName} · 附件`,
          category: item.category,
          summary: item.summary,
          meta: item.secondaryLabel || "补充材料"
        })}">${item.secondaryLabel || "附加材料"}</a>` : ""}
      </div>
    </article>
  `).join("");
}

function renderActionPlan(items) {
  const target = document.getElementById("action-plan-list");
  target.innerHTML = items.slice(0, 4).map((item) => `
    <div class="timeline-item">
      <div class="timeline-phase">${item.phase}</div>
      <div class="timeline-content">
        <strong>${item.action}</strong>
        <p>预算 ${formatMoney(item.budget)} · KPI ${item.kpi}</p>
      </div>
    </div>
  `).join("");
}

function populateCase(caseData, analysis) {
  const topChannel = analysis.channel_ranking[0];
  const topLivestream = analysis.livestream.comparison[0];
  const topStyle = analysis.xiaohongshu.find((item) => item.best) || analysis.xiaohongshu[0];
  const bestPrice = Object.entries(analysis.purchase_intent.by_price)
    .sort(([, a], [, b]) => (b.intent + b.margin) - (a.intent + a.margin))[0];

  document.getElementById("case-product-name").textContent = caseData.product.name;
  document.getElementById("case-product-note").textContent = `${caseData.product.brand} · ${caseData.product.category} · 月价 ${formatMoney(caseData.product.price_monthly)}`;
  document.getElementById("case-purchase-intent").textContent = formatPercent(analysis.purchase_intent.overall);
  document.getElementById("case-confidence").textContent = `置信度 ${formatPercent(analysis.purchase_intent.confidence)}`;
  document.getElementById("case-top-channel").textContent = topChannel.platform;
  document.getElementById("case-top-channel-note").textContent = topChannel.rec;
  document.getElementById("case-y1-revenue").textContent = formatMoney(analysis.financial.projections.y1.revenue);
  document.getElementById("case-y1-customers").textContent = `对应 ${formatCompactNumber(analysis.financial.projections.y1.customers)} 位客户`;

  document.getElementById("case-best-combo").textContent = `${topChannel.platform} + ${analysis.kol_analysis.comparison[0].type}`;
  document.getElementById("case-best-combo-note").textContent = analysis.kol_analysis.recommendation;
  document.getElementById("case-best-price").textContent = `¥${bestPrice[0]}`;
  document.getElementById("case-best-style").textContent = topStyle.style;
  document.getElementById("case-best-livestream").textContent = topLivestream.platform;
}

async function loadCaseData() {
  const [caseResponse, analysisResponse] = await Promise.all([
    fetch("cases/medislim/case_data.json"),
    fetch("cases/medislim/results/full_analysis.json")
  ]);

  const caseData = await caseResponse.json();
  const analysis = await analysisResponse.json();

  populateCase(caseData, analysis);
  renderActionPlan(analysis.action_plan);
}

function setupReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
}

function bindEndpointInteractions() {
  document.getElementById("endpoint-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-endpoint-index]");
    if (!button) return;
    renderEndpoint(Number(button.dataset.endpointIndex));
  });
}

function bindDomainInteractions() {
  document.getElementById("domain-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-domain-index]");
    if (!button) return;
    renderDomain(Number(button.dataset.domainIndex));
  });
}

function bindMaterialInteractions() {
  document.getElementById("material-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-material-index]");
    if (!button) return;
    renderMaterial(Number(button.dataset.materialIndex));
  });
}

async function init() {
  await loadContentCatalogs();
  renderEndpointMenu();
  renderEndpoint(0);
  bindEndpointInteractions();
  renderDomainMenu();
  renderDomain(0);
  bindDomainInteractions();
  renderMaterialMenu();
  renderMaterial(0);
  bindMaterialInteractions();
  renderTemplates();
  renderDeliverables();
  renderReportLibrary();
  renderSkillLibrary();
  setupReveal();

  try {
    await loadCaseData();
  } catch (error) {
    console.error("Failed to load case data", error);
  }
}

init();

// ============================================================
// Interactive Demo Engine (Browser-side simulation)
// ============================================================

function seededRandom(seed) {
  let s = seed;
  return function() {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function runDemo() {
  const productName = document.getElementById('demo-product-name').value || '测试产品';
  const category = document.getElementById('demo-category').value;
  const price = parseFloat(document.getElementById('demo-price').value) || 99;
  const popSize = parseInt(document.getElementById('demo-pop-size').value) || 1000;

  const statusEl = document.getElementById('demo-status');
  const btnEl = document.getElementById('demo-run-btn');
  const resultsEl = document.getElementById('demo-results');
  const confidenceEl = document.getElementById('demo-confidence');

  statusEl.textContent = '运行中...';
  statusEl.className = 'tag-pill tag-pill-status-checking';
  btnEl.disabled = true;
  btnEl.style.opacity = '0.6';
  resultsEl.innerHTML = '<p style="color:#818cf8;text-align:center;padding:40px 0;">正在模拟 ' + popSize + ' 位消费者决策...</p>';

  setTimeout(function() {
    const rand = seededRandom(productName.length * 137 + Math.floor(price * 100));

    // Purchase intent based on price and category
    const priceFactor = Math.max(0.3, 1 - price / 500);
    const categoryBoost = {
      '饮料': 0.15, '美妆护肤': 0.10, '保健品': 0.05,
      '食品零食': 0.12, '数码3C': -0.05, '服装鞋帽': 0.08
    };
    const baseIntent = 0.45 + priceFactor * 0.35 + (categoryBoost[category] || 0);
    const intent = Math.min(0.95, Math.max(0.15, baseIntent + (rand() - 0.5) * 0.15));
    const confidence = 0.65 + rand() * 0.25;

    // Channel analysis
    const channels = [
      { name: '小红书', roi: (2.5 + rand() * 2).toFixed(1), conversion: (4 + rand() * 6).toFixed(1) },
      { name: '抖音', roi: (2.0 + rand() * 2).toFixed(1), conversion: (3 + rand() * 5).toFixed(1) },
      { name: '天猫旗舰店', roi: (1.8 + rand() * 1.5).toFixed(1), conversion: (2 + rand() * 4).toFixed(1) },
      { name: '京东', roi: (1.5 + rand() * 1).toFixed(1), conversion: (1.5 + rand() * 3).toFixed(1) }
    ].sort(function(a, b) { return parseFloat(b.roi) - parseFloat(a.roi); });

    // KOL recommendation
    const kolTypes = [
      '中腰部垂直博主',
      '头部KOL (品牌背书)',
      '素人种草号 (真实口碑)',
      '专业人士/医生KOL'
    ];
    const selectedKol = kolTypes[Math.floor(rand() * kolTypes.length)];

    // Revenue projection
    const monthlyUnits = Math.floor(popSize * intent * 0.3 * (1 + rand() * 0.5));
    const monthlyRevenue = monthlyUnits * price;

    // Build results HTML
    let html = '';

    // Purchase Intent
    html += '<div style="margin-bottom:20px;">';
    html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">';
    html += '<span style="font-size:0.85rem;color:#94a3b8;min-width:80px;">购买意愿</span>';
    html += '<div style="flex:1;background:rgba(255,255,255,0.06);border-radius:4px;height:8px;overflow:hidden;">';
    html += '<div style="width:' + (intent * 100).toFixed(0) + '%;height:100%;background:linear-gradient(90deg,#818cf8,#a78bfa);border-radius:4px;transition:width 0.5s;"></div>';
    html += '</div>';
    html += '<strong style="color:#c4b5fd;min-width:40px;text-align:right;">' + (intent * 100).toFixed(1) + '%</strong>';
    html += '</div></div>';

    // Channel Ranking
    html += '<div style="margin-bottom:20px;">';
    html += '<span style="font-size:0.85rem;color:#94a3b8;display:block;margin-bottom:8px;">渠道排名 (按ROI)</span>';
    channels.forEach(function(ch, i) {
      const barWidth = Math.min(100, parseFloat(ch.roi) / 5 * 100);
      html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
      html += '<span style="font-size:0.8rem;color:#94a3b8;min-width:90px;">' + (i+1) + '. ' + ch.name + '</span>';
      html += '<div style="flex:1;background:rgba(255,255,255,0.04);border-radius:3px;height:6px;overflow:hidden;">';
      html += '<div style="width:' + barWidth + '%;height:100%;background:rgba(129,140,248,0.5);border-radius:3px;"></div>';
      html += '</div>';
      html += '<span style="font-size:0.75rem;color:#64748b;min-width:80px;">ROI ' + ch.roi + 'x | ' + ch.conversion + '%</span>';
      html += '</div>';
    });
    html += '</div>';

    // Key Metrics
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">';
    html += '<div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:12px;text-align:center;">';
    html += '<div style="font-size:1.5rem;font-weight:700;background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">¥' + (monthlyRevenue / 10000).toFixed(1) + '万</div>';
    html += '<div style="font-size:0.8rem;color:#94a3b8;margin-top:4px;">月收入预测</div></div>';
    html += '<div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:12px;text-align:center;">';
    html += '<div style="font-size:1.5rem;font-weight:700;background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">' + monthlyUnits.toLocaleString() + '</div>';
    html += '<div style="font-size:0.8rem;color:#94a3b8;margin-top:4px;">月销量预测</div></div>';
    html += '</div>';

    // KOL Recommendation
    html += '<div style="background:rgba(129,140,248,0.08);border:1px solid rgba(129,140,248,0.2);border-radius:8px;padding:14px;margin-bottom:16px;">';
    html += '<div style="font-size:0.85rem;color:#818cf8;margin-bottom:4px;">推荐KOL策略</div>';
    html += '<div style="color:#e0e0e0;font-size:0.95rem;">' + selectedKol + '</div>';
    html += '<div style="color:#94a3b8;font-size:0.8rem;margin-top:4px;">建议首月投入50-100篇种草内容，小规模测试后放量</div>';
    html += '</div>';

    // Recommendations
    html += '<div>';
    html += '<span style="font-size:0.85rem;color:#94a3b8;display:block;margin-bottom:8px;">策略建议</span>';
    const recs = [
      '首月聚焦' + channels[0].name + '，建立初始口碑',
      '建议定价 ¥' + price + '，' + (price < 50 ? '走量策略' : price < 200 ? '平衡策略' : '品质策略'),
      '先做 ' + Math.floor(popSize * 0.1) + ' 人小规模测试，验证后放量',
      '建立用户评价体系，收集真实反馈'
    ];
    recs.forEach(function(r) {
      html += '<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">';
      html += '<span style="color:#818cf8;margin-top:2px;">&#8226;</span>';
      html += '<span style="color:#c4b5fd;font-size:0.9rem;">' + r + '</span>';
      html += '</div>';
    });
    html += '</div>';

    resultsEl.innerHTML = html;
    confidenceEl.textContent = '置信度 ' + (confidence * 100).toFixed(0) + '%';
    statusEl.textContent = '完成';
    statusEl.className = 'tag-pill';
    btnEl.disabled = false;
    btnEl.style.opacity = '1';

    // Render charts
    document.getElementById('demo-charts-row').hidden = false;
    renderDemoCharts(intent, channels, category, rand);
  }, 800 + Math.random() * 400);
}

function renderDemoCharts(intent, channels, category, rand) {
  const chartColors = {
    purple: 'rgba(129, 140, 248, 0.8)',
    purpleLight: 'rgba(129, 140, 248, 0.2)',
    pink: 'rgba(192, 132, 252, 0.8)',
    pinkLight: 'rgba(192, 132, 252, 0.2)',
    green: 'rgba(74, 222, 128, 0.8)',
    greenLight: 'rgba(74, 222, 128, 0.2)',
    orange: 'rgba(251, 191, 36, 0.8)',
    orangeLight: 'rgba(251, 191, 36, 0.2)',
  };

  // Destroy existing charts
  const existingIntent = Chart.getChart('demo-chart-intent');
  if (existingIntent) existingIntent.destroy();
  const existingChannels = Chart.getChart('demo-chart-channels');
  if (existingChannels) existingChannels.destroy();

  // Intent by segment chart
  const segments = ['18-24', '25-30', '31-35', '36-45', '46-55'];
  const segmentIntents = segments.map(function() {
    return (intent * 100 + (rand() - 0.5) * 20).toFixed(1);
  });

  new Chart(document.getElementById('demo-chart-intent'), {
    type: 'bar',
    data: {
      labels: segments,
      datasets: [{
        label: '购买意愿 (%)',
        data: segmentIntents,
        backgroundColor: [
          chartColors.purple,
          chartColors.pink,
          chartColors.green,
          chartColors.orange,
          chartColors.purple,
        ],
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8', callback: function(v) { return v + '%'; } }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8' }
        }
      }
    }
  });

  // Channel ROI chart
  const channelNames = channels.map(function(c) { return c.name; });
  const channelRois = channels.map(function(c) { return parseFloat(c.roi); });

  new Chart(document.getElementById('demo-chart-channels'), {
    type: 'doughnut',
    data: {
      labels: channelNames,
      datasets: [{
        data: channelRois,
        backgroundColor: [
          chartColors.purple,
          chartColors.pink,
          chartColors.green,
          chartColors.orange,
        ],
        borderWidth: 0,
        spacing: 4,
      }]
    },
    options: {
      responsive: true,
      cutout: '55%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 10,
          }
        },
      }
    }
  });
}


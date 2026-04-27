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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

const AUDIO_SETTINGS_KEY = "tianyan-report-audio-settings";
const DEFAULT_PUBLIC_AUDIO_API_BASE = "https://tianyan-api.mokangmedical-dev.workers.dev";
let narrationMaterials = [];

function createBarRow(label, valueText, width) {
  return `
    <div class="bar-row">
      <div class="bar-head">
        <strong>${label}</strong>
        <span>${valueText}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${Math.max(8, Math.min(width, 100))}%"></div>
      </div>
    </div>
  `;
}

function createFactItem(title, body, note = "") {
  return `
    <article class="fact-item">
      <strong>${title}</strong>
      <p>${body}</p>
      ${note ? `<span class="fact-note">${note}</span>` : ""}
    </article>
  `;
}

function inferDefaultAudioApiBase() {
  const isGitHubPagesHost = window.location.hostname.endsWith("github.io");
  const saved = window.localStorage.getItem(AUDIO_SETTINGS_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed.apiBase) {
        if (
          isGitHubPagesHost
          && /^https?:\/\/(127\.0\.0\.1|localhost):8000$/i.test(parsed.apiBase)
        ) {
          return DEFAULT_PUBLIC_AUDIO_API_BASE;
        }
        return parsed.apiBase;
      }
    } catch {
      // ignore broken localStorage payload
    }
  }

  if (
    (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost")
    && window.location.port === "8000"
  ) {
    return window.location.origin;
  }

  return DEFAULT_PUBLIC_AUDIO_API_BASE;
}

function loadAudioSettings() {
  const defaults = {
    apiBase: inferDefaultAudioApiBase(),
    voice: "default_zh",
    instructions: "请用自然、清晰、适合商业汇报的中文女声播报。",
  };
  const saved = window.localStorage.getItem(AUDIO_SETTINGS_KEY);
  if (!saved) {
    return defaults;
  }

  try {
    return { ...defaults, ...JSON.parse(saved) };
  } catch {
    return defaults;
  }
}

function persistAudioSettings(settings) {
  window.localStorage.setItem(AUDIO_SETTINGS_KEY, JSON.stringify(settings));
}

function estimateNarrationSeconds(text) {
  const visibleChars = text.replace(/\s+/g, "").length;
  return Math.max(18, Math.round(visibleChars / 4));
}

function getAudioSettingsFromForm() {
  return {
    apiBase: document.getElementById("audio-api-base").value.trim().replace(/\/$/, ""),
    voice: document.getElementById("audio-voice").value,
    instructions: document.getElementById("audio-instructions").value.trim(),
  };
}

function setAudioConnectionState(state, label, note) {
  const tag = document.getElementById("audio-connection-tag");
  const noteElement = document.getElementById("audio-config-note");
  const configPanel = document.getElementById("audio-config-panel");
  const normalizedState = state === "available" ? "available" : (state === "checking" ? "checking" : "unavailable");

  tag.classList.remove("tag-pill-status-checking", "tag-pill-status-available", "tag-pill-status-unavailable");
  tag.classList.add(`tag-pill-status-${normalizedState}`);
  tag.textContent = label;
  noteElement.textContent = note;
  configPanel.dataset.availability = normalizedState;

  const buttons = document.querySelectorAll("[data-generate-audio]");
  buttons.forEach((button) => {
    button.disabled = normalizedState !== "available";
  });

  document.querySelectorAll(".studio-card").forEach((card) => {
    card.dataset.availability = normalizedState;
  });

  document.querySelectorAll("[data-audio-status]").forEach((statusLine) => {
    if (statusLine.textContent.startsWith("生成完成")) {
      return;
    }
    if (normalizedState === "available") {
      statusLine.textContent = "接口可用，可生成旁白";
      return;
    }
    if (normalizedState === "checking") {
      statusLine.textContent = "正在检测音频接口...";
      return;
    }
    statusLine.textContent = "接口不可用，请先检查音频服务。";
  });
}

function applyAudioSettings(settings) {
  document.getElementById("audio-api-base").value = settings.apiBase;
  document.getElementById("audio-voice").value = settings.voice;
  document.getElementById("audio-instructions").value = settings.instructions;
}

async function probeAudioHealth(settings) {
  if (!settings.apiBase) {
    setAudioConnectionState("unavailable", "不可用", "请先填写音频接口地址，再进行健康探测。");
    return { available: false };
  }

  setAudioConnectionState("checking", "检测中", `正在探测 ${settings.apiBase}/api/health ...`);

  try {
    const response = await fetch(`${settings.apiBase}/api/health`, {
      headers: {
        "Accept": "application/json",
      },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.detail || `HTTP ${response.status}`);
      error.httpStatus = response.status;
      throw error;
    }

    const audioHealth = data.media && data.media.audio ? data.media.audio : null;
    if (!audioHealth || !audioHealth.available) {
      setAudioConnectionState(
        "unavailable",
        "不可用",
        audioHealth && audioHealth.reason
          ? audioHealth.reason
          : "后端已连通，但未返回音频能力状态。",
      );
      return { available: false, health: data };
    }

    const provider = audioHealth.provider || "音频服务";
    const model = audioHealth.model || "未返回模型";
    setAudioConnectionState(
      "available",
      "可用",
      `已连通 ${settings.apiBase} · ${provider} · ${model}`,
    );
    return { available: true, health: data };
  } catch (error) {
    setAudioConnectionState(
      "unavailable",
      "不可用",
      `无法连接 ${settings.apiBase}/api/health：${error.message}`,
    );
    return { available: false, error };
  }
}

function buildNarrationMaterials(caseData, analysis) {
  const bestPrice = Object.entries(analysis.purchase_intent.by_price)
    .sort(([, a], [, b]) => (b.intent + b.margin) - (a.intent + a.margin))[0];
  const topChannel = analysis.channel_ranking[0];
  const topLivestream = analysis.livestream.comparison[0];
  const topStyle = analysis.xiaohongshu.find((item) => item.best) || analysis.xiaohongshu[0];
  const topKol = analysis.kol_analysis.comparison[0];
  const firstAction = analysis.action_plan[0];
  const topRisk = analysis.maturity_assessment.risks[0];

  return [
    {
      id: "board-brief",
      title: "60 秒董事会摘要",
      audience: "内部汇报 / 客户开场",
      note: "适合放在视频开头或管理层总结页。",
      script: `这里是天眼 Tianyan 对 ${caseData.product.name} 的上市摘要。本次模拟显示，综合购买意愿为 ${formatPercent(analysis.purchase_intent.overall)}，建议首发定价为 ${formatMoney(Number(bestPrice[0]))}。渠道上优先选择 ${topChannel.platform}，原因是匹配度最高，且更适合建立产品信任。按当前策略测算，首年收入可达到 ${formatMoney(analysis.financial.projections.y1.revenue)}。建议的第一阶段动作是 ${firstAction.action}，并围绕 ${firstAction.kpi} 做执行追踪。`,
    },
    {
      id: "channel-brief",
      title: "90 秒渠道投放稿",
      audience: "市场 / 内容 / 渠道团队",
      note: "适合做渠道策略会或投放 brief。",
      script: `渠道层面，${topChannel.platform} 是首推平台，直播建议优先放在 ${topLivestream.platform}，最佳时段为 ${topLivestream.best_time}。内容风格上，小红书最优形态是 ${topStyle.style}，互动率达到 ${formatPercent(topStyle.rate)}。KOL 组合建议从 ${topKol.type} 切入，因为它当前表现出 ${formatPercent(topKol.conversion)} 的转化率和 ${topKol.roi.toFixed(1)} 的投资回报。整体策略不是全渠道平均铺开，而是先用 ${topChannel.platform} 建立认知，再用直播完成转化收口。`,
    },
    {
      id: "risk-brief",
      title: "45 秒风险提示",
      audience: "合规 / 法务 / 项目复盘",
      note: "适合放在片尾或报告免责声明前。",
      script: `风险层面，当前整体成熟度评分为 ${analysis.maturity_assessment.overall_score} 分。首要风险是 ${topRisk.risk}，它的发生概率为 ${topRisk.prob}，影响等级为 ${topRisk.impact}。建议的缓释动作是 ${topRisk.mitigation}。需要强调的是，本报告基于公开资料与合成数据模拟，不涉及真实个人信息，结论适合作为策略判断与实验优先级参考，而不是替代真实市场执行。`,
    },
  ];
}

function renderNarrationStudio(caseData, analysis) {
  narrationMaterials = buildNarrationMaterials(caseData, analysis);
  const container = document.getElementById("narration-materials");
  container.innerHTML = narrationMaterials.map((item, index) => `
    <article class="report-panel studio-card" data-material-id="${item.id}" data-availability="checking">
      <div class="panel-row">
        <span class="panel-label">Asset ${String(index + 1).padStart(2, "0")}</span>
        <span class="tag-pill">${item.audience}</span>
      </div>
      <h3>${item.title}</h3>
      <p>${item.note}</p>
      <div class="hero-meta studio-meta">
        <span>约 ${estimateNarrationSeconds(item.script)} 秒</span>
        <span>${item.script.replace(/\s+/g, "").length} 字</span>
      </div>
      <pre class="studio-script">${escapeHtml(item.script)}</pre>
      <div class="hero-actions studio-actions">
        <button class="button button-small button-primary" type="button" data-generate-audio="${item.id}">生成旁白</button>
        <button class="button button-small button-ghost" type="button" data-copy-script="${item.id}">复制脚本</button>
      </div>
      <p class="studio-status" data-audio-status="${item.id}">正在检测音频接口...</p>
      <audio class="studio-player" data-audio-player="${item.id}" controls hidden></audio>
      <a class="text-link studio-download" data-audio-download="${item.id}" href="#" download="${item.id}.mp3" hidden>下载音频</a>
    </article>
  `).join("");
}

async function copyNarrationScript(materialId, button) {
  const material = narrationMaterials.find((item) => item.id === materialId);
  if (!material) return;

  try {
    await navigator.clipboard.writeText(material.script);
    const previous = button.textContent;
    button.textContent = "已复制";
    window.setTimeout(() => {
      button.textContent = previous;
    }, 1200);
  } catch {
    button.textContent = "复制失败";
  }
}

function base64ToBlob(base64, mimeType) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: mimeType });
}

async function generateNarration(materialId, button) {
  const material = narrationMaterials.find((item) => item.id === materialId);
  if (!material) return;

  const settings = getAudioSettingsFromForm();
  persistAudioSettings(settings);
  applyAudioSettings(settings);

  const status = document.querySelector(`[data-audio-status="${materialId}"]`);
  const player = document.querySelector(`[data-audio-player="${materialId}"]`);
  const downloadLink = document.querySelector(`[data-audio-download="${materialId}"]`);
  const previousObjectUrl = player.dataset.objectUrl;
  if (previousObjectUrl) {
    URL.revokeObjectURL(previousObjectUrl);
  }

  button.disabled = true;
  status.textContent = "正在生成旁白...";
  player.hidden = true;
  downloadLink.hidden = true;

  try {
    const response = await fetch(`${settings.apiBase}/api/v1/media/audio`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: material.script,
        voice: settings.voice,
        audio_format: "mp3",
        instructions: settings.instructions,
      }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.detail || `HTTP ${response.status}`);
      error.httpStatus = response.status;
      throw error;
    }
    if (!data.audio_base64) {
      throw new Error("接口未返回音频数据");
    }

    const blob = base64ToBlob(data.audio_base64, data.content_type || "audio/mp3");
    const objectUrl = URL.createObjectURL(blob);
    player.src = objectUrl;
    player.dataset.objectUrl = objectUrl;
    player.hidden = false;
    downloadLink.href = objectUrl;
    downloadLink.download = `${material.id}.mp3`;
    downloadLink.hidden = false;
    setAudioConnectionState("available", "可用", `旁白生成成功，当前音色 ${settings.voice}。`);
    status.textContent = `生成完成 · ${settings.voice} · ${(blob.size / 1024).toFixed(0)} KB`;
  } catch (error) {
    if (
      error.message.includes("MIMO_API_KEY")
      || error.message.includes("Failed to fetch")
      || error.httpStatus >= 500
    ) {
      setAudioConnectionState("unavailable", "不可用", error.message);
    }
    status.textContent = `生成失败：${error.message}`;
  } finally {
    button.disabled = document.getElementById("audio-config-panel").dataset.availability !== "available";
  }
}

function bindNarrationStudio() {
  const settings = loadAudioSettings();
  applyAudioSettings(settings);
  setAudioConnectionState("checking", "检测中", "正在探测音频服务健康状态...");

  document.getElementById("save-audio-config").addEventListener("click", async () => {
    const nextSettings = getAudioSettingsFromForm();
    persistAudioSettings(nextSettings);
    applyAudioSettings(nextSettings);
    await probeAudioHealth(nextSettings);
  });

  document.getElementById("copy-audio-endpoint").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const nextSettings = getAudioSettingsFromForm();
    const endpoint = `${nextSettings.apiBase}/api/v1/media/audio`;
    try {
      await navigator.clipboard.writeText(endpoint);
      const previous = button.textContent;
      button.textContent = "已复制";
      window.setTimeout(() => {
        button.textContent = previous;
      }, 1200);
    } catch {
      button.textContent = "复制失败";
    }
  });

  document.getElementById("narration-materials").addEventListener("click", async (event) => {
    const generateButton = event.target.closest("[data-generate-audio]");
    if (generateButton) {
      await generateNarration(generateButton.dataset.generateAudio, generateButton);
      return;
    }

    const copyButton = event.target.closest("[data-copy-script]");
    if (copyButton) {
      await copyNarrationScript(copyButton.dataset.copyScript, copyButton);
    }
  });

  void probeAudioHealth(settings);
}

function setupReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
}

function renderExecutive(caseData, analysis) {
  const topChannel = analysis.channel_ranking[0];
  const topLivestream = analysis.livestream.comparison[0];
  const topStyle = analysis.xiaohongshu.find((item) => item.best) || analysis.xiaohongshu[0];
  const bestPrice = Object.entries(analysis.purchase_intent.by_price)
    .sort(([, a], [, b]) => (b.intent + b.margin) - (a.intent + a.margin))[0];

  document.getElementById("report-title").textContent = analysis.meta.title;
  document.getElementById("report-subtitle").textContent = `${caseData.product.brand} · ${caseData.product.name} · ${caseData.product.form} · 月价 ${formatMoney(caseData.product.price_monthly)}`;
  document.getElementById("report-date").textContent = analysis.meta.date;
  document.getElementById("report-methodology").textContent = analysis.meta.methodology;
  document.getElementById("report-disclaimer-short").textContent = "100% 合成数据";

  document.getElementById("summary-intent").textContent = formatPercent(analysis.purchase_intent.overall);
  document.getElementById("summary-confidence").textContent = `置信度 ${formatPercent(analysis.purchase_intent.confidence)}`;
  document.getElementById("summary-price").textContent = `¥${bestPrice[0]}`;
  document.getElementById("summary-channel").textContent = topChannel.platform;
  document.getElementById("summary-channel-note").textContent = topChannel.rec;
  document.getElementById("summary-revenue").textContent = formatMoney(analysis.financial.projections.y1.revenue);
  document.getElementById("summary-customers").textContent = `${formatCompactNumber(analysis.financial.projections.y1.customers)} 位目标客户`;

  document.getElementById("executive-callouts").innerHTML = [
    {
      title: "结论一",
      body: `综合购买意愿 ${formatPercent(analysis.purchase_intent.overall)}，说明新品并非伪需求，但必须通过信任建立去提高转化。`
    },
    {
      title: "结论二",
      body: `${topChannel.platform} 排名第一，${topLivestream.platform} 在直播转化上最强，主页和详情页都应该把这两个渠道放在第一序列。`
    },
    {
      title: "结论三",
      body: `${topStyle.style} 是小红书最佳内容形态，KOL 组合建议为 ${analysis.kol_analysis.comparison[0].type} 与垂类健康博主联动。`
    }
  ].map((item) => `
    <article>
      <span class="panel-label">${item.title}</span>
      <p>${item.body}</p>
    </article>
  `).join("");
}

function renderMarket(caseData, analysis) {
  const sizes = [
    ["TAM", analysis.market_sizing.tam.value, `${analysis.market_sizing.tam.value}${analysis.market_sizing.tam.unit}`],
    ["SAM", analysis.market_sizing.sam.value, `${analysis.market_sizing.sam.value}${analysis.market_sizing.sam.unit}`],
    ["SOM Y1", analysis.market_sizing.som_y1.value, `${analysis.market_sizing.som_y1.value}${analysis.market_sizing.som_y1.unit}`],
    ["SOM Y3", analysis.market_sizing.som_y3.value, `${analysis.market_sizing.som_y3.value}${analysis.market_sizing.som_y3.unit}`]
  ];
  const maxSize = Math.max(...sizes.map(([, value]) => value));
  document.getElementById("market-size-bars").innerHTML = sizes.map(([label, value, text]) =>
    createBarRow(label, text, (value / maxSize) * 100)
  ).join("");

  // Generic real_world data rendering
  const rw = analysis.real_world || {};
  const rwItems = [];
  if (rw.obesity_2020) {
    rwItems.push(createFactItem("2020 超重/肥胖人口", `${formatCompactNumber(rw.obesity_2020.population)} 人`, `合并患病率 ${formatPercent(rw.obesity_2020.combined)}`));
  }
  if (rw.projection_2030) {
    rwItems.push(createFactItem("2030 预测", `超重与肥胖率预计达到 ${formatPercent(rw.projection_2030.combined_rate)}`));
  }
  if (rw.glp1_market_2024) {
    rwItems.push(createFactItem("中国 GLP-1 市场", `$${(rw.glp1_market_2024.usd / 1000000).toFixed(1)}M`, `2030 CAGR ${(rw.glp1_market_2024.cagr * 100).toFixed(0)}%`));
  }
  if (rw.policy) {
    rwItems.push(createFactItem("政策窗口", `${rw.policy.name} · ${rw.policy.period}`, `${rw.policy.departments} 部门联合推进`));
  }
  // Generic real_world items (for non-MediSlim cases)
  Object.entries(rw).forEach(([key, val]) => {
    if (key === 'obesity_2020' || key === 'projection_2030' || key === 'glp1_market_2024' || key === 'policy') return;
    if (val && typeof val === 'object' && val.value !== undefined) {
      rwItems.push(createFactItem(key.replace(/_/g, ' '), `${formatCompactNumber(val.value)}${val.unit || ''}`, val.source || ''));
    }
  });
  document.getElementById("real-world-facts").innerHTML = rwItems.join("");

  document.getElementById("population-segments").innerHTML = Object.entries(analysis.population.segments).map(([segment, detail]) => `
    <article class="segment-item">
      <strong>${segment}</strong>
      <p>${detail.reason}</p>
      <span>占比 ${(detail.pct * 100).toFixed(0)}% · 意愿 ${formatPercent(detail.intent)}</span>
    </article>
  `).join("");

  // Generic target_market facts
  const tm = caseData.target_market || {};
  const tmItems = [];
  if (tm.cities) tmItems.push(createFactItem("目标城市", tm.cities.join("、")));
  if (tm.bmi_range) tmItems.push(createFactItem("BMI 范围", `${tm.bmi_range[0]}-${tm.bmi_range[1]}`));
  if (tm.age_range) tmItems.push(createFactItem("年龄范围", `${tm.age_range[0]}-${tm.age_range[1]}岁`));
  if (tm.pain_points) tmItems.push(createFactItem("核心痛点", tm.pain_points.slice(0, 3).join(" · ")));
  if (tm.decision_factors) tmItems.push(createFactItem("决策因子", tm.decision_factors.join("；")));
  document.getElementById("target-market-facts").innerHTML = tmItems.join("");
}

function renderPricing(caseData, analysis) {
  const pricingCards = caseData.pricing.options.map((option) => {
    const analysisPricing = analysis.purchase_intent.by_price[String(option.price)];
    return `
      <article class="report-panel">
        <span class="panel-label">${option.strategy}</span>
        <h3>¥${option.price}</h3>
        <p>转化 ${formatPercent(analysisPricing.intent)} · 毛利 ${(analysisPricing.margin * 100).toFixed(0)}%</p>
        <p>${analysisPricing.perception}</p>
        <p>风险：${option.risk}</p>
      </article>
    `;
  }).join("");
  document.getElementById("pricing-grid").innerHTML = pricingCards;
}

function renderChannels(analysis) {
  const maxChannel = Math.max(...analysis.channel_ranking.map((item) => item.score));
  document.getElementById("channel-ranking-bars").innerHTML = analysis.channel_ranking.map((item) =>
    createBarRow(item.platform, `${item.score.toFixed(3)} · ${item.rec}`, (item.score / maxChannel) * 100)
  ).join("");

  document.getElementById("livestream-grid").innerHTML = analysis.livestream.comparison.map((item) => `
    <article>
      <strong>${item.platform}</strong>
      <p>GMV ${formatMoney(item.gmv)} · 转化 ${formatPercent(item.conversion)}</p>
      <p>${item.best_time} · ${item.recommend}</p>
    </article>
  `).join("");

  document.getElementById("kol-table").innerHTML = `
    <thead>
      <tr>
        <th>类型</th>
        <th>互动率</th>
        <th>转化率</th>
        <th>ROI</th>
        <th>建议</th>
      </tr>
    </thead>
    <tbody>
      ${analysis.kol_analysis.comparison.map((item) => `
        <tr>
          <td>${item.type}</td>
          <td>${formatPercent(item.engagement)}</td>
          <td>${formatPercent(item.conversion)}</td>
          <td>${item.roi.toFixed(1)}</td>
          <td>${item.recommend}</td>
        </tr>
      `).join("")}
    </tbody>
  `;

  const maxXhs = Math.max(...analysis.xiaohongshu.map((item) => item.rate));
  document.getElementById("xiaohongshu-bars").innerHTML = analysis.xiaohongshu.map((item) =>
    createBarRow(item.style, `${formatPercent(item.rate)} · ${formatCompactNumber(item.interactions)} 互动`, (item.rate / maxXhs) * 100)
  ).join("");
}

function renderCompetition(caseData, analysis) {
  const baseCompetitors = new Map(caseData.competitors.map((item) => [item.name.split("（")[0], item]));
  document.getElementById("competitor-table").innerHTML = `
    <thead>
      <tr>
        <th>竞品</th>
        <th>月价</th>
        <th>剂型</th>
        <th>份额</th>
        <th>认知度</th>
        <th>威胁等级</th>
      </tr>
    </thead>
    <tbody>
      ${analysis.competitors.map((item) => {
        const source = baseCompetitors.get(item.name) || {};
        return `
          <tr>
            <td>${item.name}</td>
            <td>${formatMoney(source.price_monthly || item.price)}</td>
            <td>${source.form || item.form}</td>
            <td>${formatPercent(item.share)}</td>
            <td>${formatPercent(item.awareness)}</td>
            <td>${item.threat}</td>
          </tr>
        `;
      }).join("")}
    </tbody>
  `;
}

function renderExecution(analysis) {
  document.getElementById("execution-timeline").innerHTML = analysis.action_plan.map((item) => `
    <div class="timeline-item">
      <div class="timeline-phase">${item.phase}</div>
      <div class="timeline-content">
        <strong>${item.action}</strong>
        <p>预算 ${formatMoney(item.budget)} · KPI ${item.kpi}</p>
      </div>
    </div>
  `).join("");

  const unit = analysis.financial.unit_economics;
  const projections = analysis.financial.projections;
  document.getElementById("finance-grid").innerHTML = [
    { title: "毛利率", body: formatPercent(unit.gross_margin) },
    { title: "CAC", body: formatMoney(unit.cac) },
    { title: "LTV", body: formatMoney(unit.ltv) },
    { title: "LTV/CAC", body: unit.ltv_cac_ratio.toFixed(2) },
    { title: "回本周期", body: `${unit.payback_months} 个月` },
    { title: "Y3 收入", body: formatMoney(projections.y3.revenue) }
  ].map((item) => `
    <article class="finance-item">
      <strong>${item.title}</strong>
      <p>${item.body}</p>
    </article>
  `).join("");
}

function renderRisks(analysis) {
  document.getElementById("overall-score").textContent = `${analysis.maturity_assessment.overall_score}`;
  const dimensions = Object.entries(analysis.maturity_assessment.dimensions);
  document.getElementById("maturity-bars").innerHTML = dimensions.map(([label, detail]) =>
    createBarRow(label, `${detail.score} · ${detail.note}`, detail.score)
  ).join("");

  document.getElementById("risk-list").innerHTML = analysis.maturity_assessment.risks.map((item) => `
    <article class="risk-item">
      <div class="risk-meta">
        <span>概率 ${item.prob}</span>
        <span>影响 ${item.impact}</span>
      </div>
      <strong>${item.risk}</strong>
      <p>缓释：${item.mitigation}</p>
    </article>
  `).join("");
}

function renderMethodology(caseData, analysis) {
  document.getElementById("source-list").innerHTML = analysis.meta.data_sources.map((source) => `<li>${source}</li>`).join("");
  document.getElementById("report-disclaimer-full").textContent = caseData.disclaimer;
}

async function init() {
  setupReveal();
  const [caseResponse, analysisResponse] = await Promise.all([
    fetch("./case_data.json"),
    fetch("./results/full_analysis.json")
  ]);

  const caseData = await caseResponse.json();
  const analysis = await analysisResponse.json();

  renderExecutive(caseData, analysis);
  renderNarrationStudio(caseData, analysis);
  renderMarket(caseData, analysis);
  renderPricing(caseData, analysis);
  renderChannels(analysis);
  renderCompetition(caseData, analysis);
  renderExecution(analysis);
  renderRisks(analysis);
  renderMethodology(caseData, analysis);
  bindNarrationStudio();
}

init().catch((error) => {
  console.error("Failed to initialize report page", error);
});

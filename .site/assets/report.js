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

  document.getElementById("real-world-facts").innerHTML = [
    createFactItem("2020 超重/肥胖人口", `${formatCompactNumber(analysis.real_world.obesity_2020.population)} 人`, `合并患病率 ${formatPercent(analysis.real_world.obesity_2020.combined)}`),
    createFactItem("2030 预测", `超重与肥胖率预计达到 ${formatPercent(analysis.real_world.projection_2030.combined_rate)}`),
    createFactItem("中国 GLP-1 市场", `$${(analysis.real_world.glp1_market_2024.usd / 1000000).toFixed(1)}M`, `2030 CAGR ${(analysis.real_world.glp1_market_2024.cagr * 100).toFixed(0)}%`),
    createFactItem("政策窗口", `${analysis.real_world.policy.name} · ${analysis.real_world.policy.period}`, `${analysis.real_world.policy.departments} 部门联合推进`)
  ].join("");

  document.getElementById("population-segments").innerHTML = Object.entries(analysis.population.segments).map(([segment, detail]) => `
    <article class="segment-item">
      <strong>${segment}</strong>
      <p>${detail.reason}</p>
      <span>占比 ${(detail.pct * 100).toFixed(0)}% · 意愿 ${formatPercent(detail.intent)}</span>
    </article>
  `).join("");

  document.getElementById("target-market-facts").innerHTML = [
    createFactItem("目标城市", caseData.target_market.cities.join("、")),
    createFactItem("BMI 范围", `${caseData.target_market.bmi_range[0]}-${caseData.target_market.bmi_range[1]}`),
    createFactItem("核心痛点", caseData.target_market.pain_points.slice(0, 3).join(" · ")),
    createFactItem("决策因子", caseData.target_market.decision_factors.join("；"))
  ].join("");
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
  renderMarket(caseData, analysis);
  renderPricing(caseData, analysis);
  renderChannels(analysis);
  renderCompetition(caseData, analysis);
  renderExecution(analysis);
  renderRisks(analysis);
  renderMethodology(caseData, analysis);
}

init().catch((error) => {
  console.error("Failed to initialize report page", error);
});

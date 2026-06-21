async function loadCampaignData() {
  const response = await fetch("../content/growth-campaigns.json");
  if (!response.ok) {
    throw new Error(`Failed to load campaign data: ${response.status}`);
  }
  return response.json();
}

function renderSummary(container, summary) {
  container.innerHTML = `
    <article class="metric-panel">
      <span class="metric-label">目标</span>
      <strong class="metric-value">${summary.goal}</strong>
      <p class="metric-note">宣传主目标</p>
    </article>
    <article class="metric-panel">
      <span class="metric-label">关键指标</span>
      <strong class="metric-value">${summary.primaryKpi}</strong>
      <p class="metric-note">优先看的执行指标</p>
    </article>
    <article class="metric-panel">
      <span class="metric-label">节奏</span>
      <strong class="metric-value">${summary.cadence}</strong>
      <p class="metric-note">建议执行频率</p>
    </article>
  `;
}

function renderCalendar(container, items) {
  container.innerHTML = items.map((item) => `
    <article class="course-card">
      <span class="panel-label">${item.day}</span>
      <h3>${item.theme}</h3>
      <p>${item.format} · ${item.hook}</p>
      <div class="course-meta">
        <span>CTA</span>
        <span>${item.cta}</span>
      </div>
    </article>
  `).join("");
}

function renderScripts(container, items) {
  container.innerHTML = items.map((item) => `
    <article class="report-panel">
      <div class="panel-row">
        <span class="panel-label">${item.type || item.duration}</span>
        <button class="button button-small button-ghost" type="button" data-copy-script="${item.title}">复制脚本</button>
      </div>
      <h3>${item.title}</h3>
      ${item.scene ? `<p class="section-body">${item.scene}</p>` : ""}
      <pre class="studio-script">${item.script}</pre>
    </article>
  `).join("");

  container.querySelectorAll("[data-copy-script]").forEach((button, index) => {
    button.addEventListener("click", async () => {
      const script = items[index].script;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(script);
        button.textContent = "已复制";
        setTimeout(() => {
          button.textContent = original;
        }, 1200);
      } catch {
        button.textContent = "复制失败";
      }
    });
  });
}

function getCampaignKey() {
  return document.body.dataset.campaign;
}

async function initCampaignPage() {
  const key = getCampaignKey();
  if (!key) return;

  const data = await loadCampaignData();
  const campaign = data[key];
  if (!campaign) return;

  const summary = document.getElementById("campaign-summary-grid");
  if (summary && campaign.summary) {
    renderSummary(summary, campaign.summary);
  }

  const calendar = document.getElementById("campaign-calendar-grid");
  if (calendar && campaign.calendar) {
    renderCalendar(calendar, campaign.calendar);
  }

  const scripts = document.getElementById("campaign-script-grid");
  if (scripts && campaign.scripts) {
    renderScripts(scripts, campaign.scripts);
  }

  const packs = document.getElementById("campaign-pack-grid");
  if (packs && campaign.packs) {
    renderScripts(packs, campaign.packs);
  }
}

initCampaignPage().catch((error) => {
  console.error("Failed to initialize campaign page", error);
});

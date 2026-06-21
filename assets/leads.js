function buildLeadQuery() {
  const status = document.getElementById("lead-filter-status")?.value || "";
  const owner = document.getElementById("lead-filter-owner")?.value.trim() || "";
  const query = document.getElementById("lead-filter-query")?.value.trim() || "";
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (owner) params.set("owner", owner);
  if (query) params.set("q", query);
  return params.toString();
}

async function loadLeads() {
  const query = buildLeadQuery();
  const response = await fetch(`http://127.0.0.1:8000/api/v1/leads${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error(`Failed to load leads: ${response.status}`);
  }
  return response.json();
}

async function loadLeadSummary() {
  const response = await fetch("http://127.0.0.1:8000/api/v1/leads/pipeline/summary");
  if (!response.ok) {
    throw new Error(`Failed to load lead summary: ${response.status}`);
  }
  return response.json();
}

async function loadLeadHistory(leadId) {
  const response = await fetch(`http://127.0.0.1:8000/api/v1/leads/${leadId}/history`);
  if (!response.ok) {
    throw new Error(`Failed to load lead history: ${response.status}`);
  }
  return response.json();
}

function formatTimestamp(value) {
  if (!value) return "--";
  return new Date(value * 1000).toLocaleString("zh-CN");
}

function renderLeadSummary(summary) {
  const grid = document.getElementById("lead-summary-grid");
  const entries = Object.entries(summary);
  grid.innerHTML = entries.map(([status, count]) => `
    <article class="metric-panel">
      <span class="metric-label">${status}</span>
      <strong class="metric-value">${count}</strong>
      <p class="metric-note">当前状态数量</p>
    </article>
  `).join("");
}

async function updateLead(leadId, payload, statusNode) {
  statusNode.textContent = "更新中...";
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/v1/leads/${leadId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.detail || "更新失败");
    }
    statusNode.textContent = "已更新";
    await initLeadsPage();
  } catch (error) {
    statusNode.textContent = `更新失败：${error.message}`;
  }
}

async function toggleHistory(leadId, target) {
  if (target.dataset.loaded === "true") {
    target.hidden = !target.hidden;
    return;
  }
  target.textContent = "加载历史中...";
  target.hidden = false;
  try {
    const data = await loadLeadHistory(leadId);
    const items = data.history || [];
    target.innerHTML = items.length
      ? items.map((item) => `
        <div class="bullet-stack">
          <span>${item.status} · ${item.owner || "未分配"} · ${formatTimestamp(item.updated_at)}</span>
          <span>${item.note || "无备注"}</span>
        </div>
      `).join("")
      : "<p class='section-body'>暂无历史记录。</p>";
    target.dataset.loaded = "true";
  } catch (error) {
    target.textContent = `加载失败：${error.message}`;
  }
}

function renderLeads(leads) {
  const grid = document.getElementById("lead-list-grid");
  const count = document.getElementById("lead-list-count");
  count.textContent = `${leads.length} leads`;

  if (!leads.length) {
    grid.innerHTML = `<article class="report-panel"><p class="section-body">暂无线索。</p></article>`;
    return;
  }

  grid.innerHTML = leads.map((lead) => `
    <article class="report-panel">
      <div class="panel-row">
        <span class="panel-label">${lead.project_type}</span>
        <span class="tag-pill">${lead.status || "new"}</span>
      </div>
      <h3>${lead.company_name}</h3>
      <p class="section-body">${lead.contact_name} · ${lead.contact_channel}</p>
      <div class="bullet-stack">
        <span>意向套餐：${lead.preferred_offer || "未填写"}</span>
        <span>预算范围：${lead.budget_range}</span>
        <span>项目目标：${lead.goals}</span>
        <span>负责人：${lead.owner || "未分配"}</span>
        <span>备注：${lead.note || "暂无备注"}</span>
        <span>提交时间：${formatTimestamp(lead.created_at)}</span>
        <span>最近更新：${formatTimestamp(lead.updated_at)}</span>
        <span>线索编号：${lead.lead_id}</span>
      </div>
      <div class="studio-actions">
        <button class="button button-small button-ghost" type="button" data-history-button="${lead.lead_id}">查看跟进历史</button>
      </div>
      <div class="library-grid" id="lead-history-${lead.lead_id}" hidden></div>
      <form class="studio-form lead-update-form" data-lead-id="${lead.lead_id}">
        <label class="studio-field">
          <span>状态</span>
          <select class="studio-input" name="status">
            ${["new", "contacted", "proposal", "won", "lost"].map((item) => `<option value="${item}" ${lead.status === item ? "selected" : ""}>${item}</option>`).join("")}
          </select>
        </label>
        <label class="studio-field">
          <span>负责人</span>
          <input class="studio-input" name="owner" value="${lead.owner || ""}">
        </label>
        <label class="studio-field">
          <span>备注</span>
          <textarea class="studio-input studio-textarea" name="note">${lead.note || ""}</textarea>
        </label>
        <div class="studio-actions">
          <button class="button button-small button-primary" type="submit">更新线索</button>
        </div>
        <p class="studio-status" data-lead-update-status="${lead.lead_id}">待更新</p>
      </form>
    </article>
  `).join("");

  grid.querySelectorAll(".lead-update-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const leadId = form.dataset.leadId;
      const statusNode = form.querySelector(`[data-lead-update-status="${leadId}"]`);
      await updateLead(leadId, {
        status: form.status.value,
        owner: form.owner.value.trim(),
        note: form.note.value.trim(),
      }, statusNode);
    });
  });

  grid.querySelectorAll("[data-history-button]").forEach((button) => {
    button.addEventListener("click", async () => {
      const leadId = button.dataset.historyButton;
      const target = document.getElementById(`lead-history-${leadId}`);
      await toggleHistory(leadId, target);
    });
  });
}

function bindFilters() {
  const form = document.getElementById("lead-filter-form");
  const exportLink = document.getElementById("lead-export-link");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = buildLeadQuery();
    exportLink.href = `http://127.0.0.1:8000/api/v1/leads/export.csv${query ? `?${query}` : ""}`;
    await initLeadsPage();
  });
}

async function initLeadsPage() {
  const status = document.getElementById("lead-list-status");
  status.textContent = "加载中...";
  try {
    const [summaryData, leadData] = await Promise.all([loadLeadSummary(), loadLeads()]);
    renderLeadSummary(summaryData.summary || {});
    renderLeads(leadData.leads || []);
    status.textContent = "已连接 Tianyan 后端。";
  } catch (error) {
    status.textContent = `加载失败：${error.message}`;
  }
}

bindFilters();
initLeadsPage().catch((error) => {
  console.error("Failed to initialize leads page", error);
});

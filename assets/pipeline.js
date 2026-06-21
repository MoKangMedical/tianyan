const PIPELINE_STATUSES = ["new", "contacted", "proposal", "won", "lost"];

async function loadPipelineLeads() {
  const response = await fetch("http://127.0.0.1:8000/api/v1/leads");
  if (!response.ok) {
    throw new Error(`Failed to load pipeline leads: ${response.status}`);
  }
  return response.json();
}

function formatTime(ts) {
  if (!ts) return "--";
  return new Date(ts * 1000).toLocaleString("zh-CN");
}

function groupByStatus(leads) {
  const groups = Object.fromEntries(PIPELINE_STATUSES.map((status) => [status, []]));
  leads.forEach((lead) => {
    const status = PIPELINE_STATUSES.includes(lead.status) ? lead.status : "new";
    groups[status].push(lead);
  });
  return groups;
}

function renderBoard(leads) {
  const root = document.getElementById("pipeline-board");
  const groups = groupByStatus(leads);
  root.innerHTML = PIPELINE_STATUSES.map((status) => `
    <section class="report-panel">
      <div class="panel-row">
        <span class="panel-label">${status}</span>
        <span class="tag-pill">${groups[status].length}</span>
      </div>
      <div class="library-grid">
        ${groups[status].length ? groups[status].map((lead) => `
          <article class="library-card">
            <strong>${lead.company_name}</strong>
            <small>${lead.project_type} · ${lead.budget_range}</small>
            <span>${lead.contact_name} · ${lead.contact_channel}</span>
            <span>负责人：${lead.owner || "未分配"}</span>
            <span>最近更新：${formatTime(lead.updated_at || lead.created_at)}</span>
            <span>${lead.note || "暂无备注"}</span>
          </article>
        `).join("") : `<div class="viewer-empty">暂无线索</div>`}
      </div>
    </section>
  `).join("");
}

async function initPipelinePage() {
  const status = document.getElementById("pipeline-status");
  status.textContent = "加载中...";
  try {
    const data = await loadPipelineLeads();
    renderBoard(data.leads || []);
    status.textContent = `已加载 ${data.count} 条线索。`;
  } catch (error) {
    status.textContent = `加载失败：${error.message}`;
  }
}

initPipelinePage().catch((error) => {
  console.error("Failed to initialize pipeline page", error);
});

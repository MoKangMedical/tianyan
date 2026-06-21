async function loadOffers() {
  const response = await fetch("../content/offers-catalog.json");
  if (!response.ok) {
    throw new Error(`Failed to load offers: ${response.status}`);
  }
  return response.json();
}

function renderOffers(offers) {
  const grid = document.getElementById("offer-grid");
  grid.innerHTML = offers.map((offer) => `
    <article class="course-card">
      <span class="panel-label">${offer.timeline}</span>
      <h3>${offer.name}</h3>
      <p>${offer.fit}</p>
      <div class="course-meta">
        <span>${offer.price}</span>
        <span>${offer.key}</span>
      </div>
      <div class="bullet-stack">
        ${offer.deliverables.map((item) => `<span>${item}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

async function submitLead(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.getElementById("lead-status");
  const payload = {
    company_name: form.company_name.value.trim(),
    contact_name: form.contact_name.value.trim(),
    contact_channel: form.contact_channel.value.trim(),
    project_type: form.project_type.value.trim(),
    budget_range: form.budget_range.value.trim(),
    goals: form.goals.value.trim(),
    preferred_offer: form.preferred_offer.value.trim(),
  };

  status.textContent = "提交中...";

  try {
    const response = await fetch("http://127.0.0.1:8000/api/v1/leads/intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.detail || "提交失败");
    }
    status.textContent = `已提交，线索编号 ${data.lead_id}`;
    form.reset();
  } catch (error) {
    status.textContent = `提交失败：${error.message}`;
  }
}

async function initContactPage() {
  const offers = await loadOffers();
  renderOffers(offers.offers || []);
  document.getElementById("lead-form").addEventListener("submit", submitLead);
}

initContactPage().catch((error) => {
  console.error("Failed to initialize contact page", error);
});

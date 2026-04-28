function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function resolveRepoPath(target, currentPath) {
  if (!target || target.startsWith("#")) {
    return target;
  }

  if (/^(https?:|mailto:|tel:)/i.test(target)) {
    return target;
  }

  const [pathPart, fragment] = target.split("#");

  if (!pathPart) {
    return fragment ? `#${fragment}` : target;
  }

  let resolvedPath = pathPart;

  if (pathPart.startsWith("/")) {
    resolvedPath = pathPart.replace(/^\/+/, "");
  } else {
    const baseDirectory = currentPath.includes("/")
      ? currentPath.slice(0, currentPath.lastIndexOf("/") + 1)
      : "";
    resolvedPath = new URL(pathPart, `https://repo.local/${baseDirectory}`).pathname.replace(/^\/+/, "");
  }

  return fragment ? `${resolvedPath}#${fragment}` : resolvedPath;
}

function buildViewerHref(path, mode = "source") {
  const params = new URLSearchParams({
    path,
    mode
  });

  return `viewer.html?${params.toString()}`;
}

function resolveMarkdownHref(target, currentPath) {
  if (!target) {
    return "#";
  }

  if (target.startsWith("#") || /^(https?:|mailto:|tel:)/i.test(target)) {
    return target;
  }

  const resolved = resolveRepoPath(target, currentPath);
  const [resolvedPath, fragment] = resolved.split("#");
  const suffix = fragment ? `#${fragment}` : "";

  if (/\.(md|json)$/i.test(resolvedPath)) {
    return `${buildViewerHref(resolvedPath, "source")}${suffix}`;
  }

  return `${resolveAssetPath(resolvedPath)}${suffix}`;
}

function renderInlineMarkdown(value, currentPath = "") {
  let html = escapeHtml(value);

  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => {
    const resolvedHref = resolveMarkdownHref(href, currentPath);
    const isExternal = /^(https?:|mailto:|tel:)/i.test(resolvedHref);
    const target = isExternal ? ' target="_blank" rel="noreferrer"' : "";
    return `<a href="${resolvedHref}"${target}>${escapeHtml(label)}</a>`;
  });

  return html;
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

function resolveAssetPath(path) {
  const encodedPath = path
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");

  return `../${encodedPath}`;
}

function parseTableRow(line, currentPath) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => renderInlineMarkdown(cell.trim(), currentPath));
}

function renderTable(lines, currentPath) {
  const rows = lines.filter((_, index) => index !== 1).map((line) => parseTableRow(line, currentPath));
  const head = rows[0] || [];
  const body = rows.slice(1);

  return `
    <div class="table-wrap">
      <table class="data-table markdown-table">
        <thead>
          <tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function isTableStart(lines, index) {
  if (!/^\s*\|.*\|\s*$/.test(lines[index] || "")) {
    return false;
  }

  return /^\s*\|?[\s:-|]+\|?\s*$/.test(lines[index + 1] || "");
}

function isSpecialMarkdownLine(line) {
  return /^#{1,6}\s+/.test(line)
    || /^>\s?/.test(line)
    || /^\s*[-*]\s+/.test(line)
    || /^\s*\d+\.\s+/.test(line)
    || /^\s*---+\s*$/.test(line)
    || /^```/.test(line);
}

function renderMarkdown(markdown, currentPath) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (/^```/.test(line)) {
      const language = line.replace(/^```/, "").trim();
      const codeLines = [];
      index += 1;

      while (index < lines.length && !/^```/.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }

      blocks.push(`
        <pre class="viewer-pre"><code class="language-${escapeHtml(language || "text")}">${escapeHtml(codeLines.join("\n"))}</code></pre>
      `);
      index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const tableLines = [lines[index], lines[index + 1]];
      index += 2;

      while (index < lines.length && /^\s*\|.*\|\s*$/.test(lines[index] || "")) {
        tableLines.push(lines[index]);
        index += 1;
      }

      blocks.push(renderTable(tableLines, currentPath));
      continue;
    }

    if (/^#{1,6}\s+/.test(line)) {
      const [, hashes, text] = line.match(/^(#{1,6})\s+(.+)$/) || [];
      const level = hashes.length;
      blocks.push(`<h${level}>${renderInlineMarkdown(text, currentPath)}</h${level}>`);
      index += 1;
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quoteLines = [];

      while (index < lines.length && /^>\s?/.test(lines[index] || "")) {
        quoteLines.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }

      blocks.push(`
        <blockquote>
          ${quoteLines.map((quoteLine) => `<p>${renderInlineMarkdown(quoteLine, currentPath)}</p>`).join("")}
        </blockquote>
      `);
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];

      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index] || "")) {
        items.push(lines[index].replace(/^\s*[-*]\s+/, ""));
        index += 1;
      }

      blocks.push(`<ul>${items.map((item) => `<li>${renderInlineMarkdown(item, currentPath)}</li>`).join("")}</ul>`);
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];

      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index] || "")) {
        items.push(lines[index].replace(/^\s*\d+\.\s+/, ""));
        index += 1;
      }

      blocks.push(`<ol>${items.map((item) => `<li>${renderInlineMarkdown(item, currentPath)}</li>`).join("")}</ol>`);
      continue;
    }

    if (/^\s*---+\s*$/.test(line)) {
      blocks.push("<hr>");
      index += 1;
      continue;
    }

    const paragraph = [];
    while (
      index < lines.length
      && lines[index].trim()
      && !isSpecialMarkdownLine(lines[index])
      && !isTableStart(lines, index)
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }

    blocks.push(`<p>${renderInlineMarkdown(paragraph.join(" "), currentPath)}</p>`);
  }

  return blocks.join("\n");
}

function collectJsonFacts(data) {
  const facts = [];

  if (typeof data?.n_results === "number") {
    facts.push({ label: "结果条目", value: data.n_results });
  }

  if (Array.isArray(data?.results)) {
    const tasks = new Set(data.results.map((item) => item.task).filter(Boolean));
    const models = new Set(data.results.map((item) => item.model).filter(Boolean));
    const datasets = new Set(data.results.map((item) => item.dataset).filter(Boolean));

    facts.push({ label: "记录数", value: data.results.length });
    if (tasks.size) facts.push({ label: "任务数", value: tasks.size });
    if (models.size) facts.push({ label: "模型数", value: models.size });
    if (datasets.size) facts.push({ label: "数据集", value: datasets.size });
  }

  if (data?.product?.name) {
    facts.push({ label: "产品", value: data.product.name });
  }

  if (typeof data?.purchase_intent?.overall === "number") {
    facts.push({ label: "购买意愿", value: `${(data.purchase_intent.overall * 100).toFixed(1)}%` });
  }

  if (data?.financial?.projections?.y1?.revenue) {
    facts.push({ label: "Y1 收入", value: formatMoney(data.financial.projections.y1.revenue) });
  }

  if (Array.isArray(data?.action_plan)) {
    facts.push({ label: "行动阶段", value: data.action_plan.length });
  }

  return facts.slice(0, 4);
}

function renderFacts(facts) {
  const container = document.getElementById("viewer-facts");

  if (!facts.length) {
    container.innerHTML = `
      <article class="viewer-fact">
        <span>文件类型</span>
        <strong>可浏览资料</strong>
      </article>
    `;
    return;
  }

  container.innerHTML = facts.map((fact) => `
    <article class="viewer-fact">
      <span>${fact.label}</span>
      <strong>${fact.value}</strong>
    </article>
  `).join("");
}

function detectFileType(path) {
  if (/\.json$/i.test(path)) return "JSON";
  if (/\.md$/i.test(path)) return "Markdown";
  return "Document";
}

function getModeLabel(mode) {
  if (mode === "skill") return "Skill Viewer";
  if (mode === "source") return "Source Viewer";
  return "Report Viewer";
}

async function init() {
  const params = new URLSearchParams(window.location.search);
  const path = params.get("path");
  const title = params.get("title") || "资料浏览";
  const category = params.get("category") || "内容";
  const summary = params.get("summary") || "仓库内资料的结构化浏览视图。";
  const meta = params.get("meta") || "原始文件";
  const mode = params.get("mode") || "report";

  const titleElement = document.getElementById("viewer-title");
  const summaryElement = document.getElementById("viewer-summary");
  const categoryElement = document.getElementById("viewer-category");
  const pathElement = document.getElementById("viewer-path");
  const typeElement = document.getElementById("viewer-type");
  const noteElement = document.getElementById("viewer-note");
  const sourceLink = document.getElementById("viewer-source-link");
  const rawLink = document.getElementById("viewer-raw-link");
  const modeLabel = document.getElementById("viewer-mode-label");
  const rendered = document.getElementById("viewer-rendered");

  titleElement.textContent = title;
  summaryElement.textContent = summary;
  categoryElement.textContent = category;
  modeLabel.textContent = getModeLabel(mode);

  if (!path) {
    typeElement.textContent = "Missing Path";
    pathElement.textContent = "未提供 path 参数";
    noteElement.textContent = "需要通过站内能力库入口进入，才能定位要浏览的材料。";
    rendered.innerHTML = `<div class="viewer-empty">没有可加载的内容。</div>`;
    renderFacts([]);
    return;
  }

  const assetPath = resolveAssetPath(path);
  const fileType = detectFileType(path);

  typeElement.textContent = fileType;
  pathElement.textContent = path;
  noteElement.textContent = meta;
  sourceLink.href = assetPath;
  rawLink.href = assetPath;

  try {
    if (fileType === "JSON") {
      const response = await fetch(assetPath);
      if (!response.ok) {
        throw new Error(`Failed to load ${path}: ${response.status}`);
      }

      const data = await response.json();
      renderFacts(collectJsonFacts(data));
      rendered.innerHTML = `<pre class="viewer-pre"><code>${escapeHtml(JSON.stringify(data, null, 2))}</code></pre>`;
      return;
    }

    const response = await fetch(assetPath);
    if (!response.ok) {
      throw new Error(`Failed to load ${path}: ${response.status}`);
    }

    const text = await response.text();
    renderFacts([]);
    rendered.innerHTML = fileType === "Markdown"
      ? renderMarkdown(text, path)
      : `<pre class="viewer-pre"><code>${escapeHtml(text)}</code></pre>`;
  } catch (error) {
    console.error("Failed to load viewer content", error);
    renderFacts([]);
    rendered.innerHTML = `
      <div class="viewer-empty">
        无法加载该文件。请直接打开原始文件，或检查路径是否仍然存在。
      </div>
    `;
  }
}

init();

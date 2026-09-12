const thread = document.getElementById("thread");
const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const sourceList = document.getElementById("source-list");
const ingestStatus = document.getElementById("ingest-status");
const docMeta = document.getElementById("doc-meta");
const modeSelect = document.getElementById("mode-select");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const docsMore = document.getElementById("docs-more");

let allSources = [];
let hasLlm = false;
let hasHuggingFace = false;
let docsExpanded = false;
const MAX_QUESTIONS = 10;
const INITIAL_DOCS = 5;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function kindLabel(kind) {
  if (kind === "docx" || kind === "doc") return "W";
  if (kind === "pdf") return "PDF";
  if (["xlsx", "xls", "xlsm", "csv"].includes(kind)) return "X";
  return "MD";
}

function renderSources() {
  const q = document.getElementById("doc-search").value.trim().toLowerCase();
  const sort = document.getElementById("doc-sort").value;
  let rows = allSources.filter((s) => !q || s.name.toLowerCase().includes(q) || s.path.toLowerCase().includes(q));
  if (sort === "name") rows = [...rows].sort((a, b) => a.name.localeCompare(b.name));
  if (sort === "chunks") rows = [...rows].sort((a, b) => b.chunks - a.chunks);
  if (sort === "added") rows = [...rows].sort((a, b) => (b.added || 0) - (a.added || 0));

  const visibleRows = docsExpanded ? rows : rows.slice(0, INITIAL_DOCS);
  sourceList.classList.toggle("expanded", docsExpanded);
  docsMore.hidden = rows.length <= INITIAL_DOCS;
  docsMore.textContent = docsExpanded ? "Show less" : `See more (${rows.length - INITIAL_DOCS})`;

  sourceList.innerHTML = visibleRows
    .map(
      (s) => `<li class="doc-row">
        <span class="file-ico ${escapeHtml(s.kind)}">${kindLabel(s.kind)}</span>
        <div>
          <div class="doc-name">${escapeHtml(s.name)}</div>
          <div class="doc-sub"><span class="tag ${escapeHtml(s.category)}">${escapeHtml(s.category)}</span><span>${escapeHtml(s.path)}</span></div>
        </div>
        <div class="doc-meta-right"><strong>${s.chunks} chunks</strong>${escapeHtml(s.date || "")}</div>
        ${s.deletable ? `<button class="kebab" data-del="${escapeHtml(s.source)}" title="Remove">⋮</button>` : `<span></span>`}
      </li>`
    )
    .join("");
}

async function refreshSources() {
  const [health, sources] = await Promise.all([
    fetch("/api/health").then((r) => r.json()),
    fetch("/api/sources").then((r) => r.json()),
  ]);
  hasLlm = Boolean(health.llm);
  hasHuggingFace = Boolean(health.huggingface);
  allSources = sources.sources || [];
  const nChunks = sources.chunk_count ?? 0;
  docMeta.textContent = `${nChunks} chunks indexed`;
  modeSelect.value = hasHuggingFace ? "huggingface" : "extractive";
  renderSources();
}

function addMessage(role, html) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  wrap.innerHTML = `<div class="bubble">${html}</div>`;
  thread.appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return wrap;
}

function trimChatHistory() {
  const questions = [...thread.querySelectorAll(".msg.user")];
  while (questions.length > MAX_QUESTIONS) {
    const oldestQuestion = questions.shift();
    const oldestAnswer = oldestQuestion.nextElementSibling;
    oldestQuestion.remove();
    if (oldestAnswer?.classList.contains("assistant")) oldestAnswer.remove();
  }
}

async function ask(question) {
  let mode = modeSelect.value;
  if (mode === "openai" && !hasLlm) {
    ingestStatus.textContent = "Add an OpenAI key in Settings for synthesized answers.";
    document.getElementById("settings-dialog").showModal();
    mode = hasHuggingFace ? "huggingface" : "extractive";
  }
  if (mode === "huggingface" && !hasHuggingFace) {
    ingestStatus.textContent = "Hugging Face models are still being prepared. Try again shortly.";
    mode = "extractive";
  }
  addMessage("user", escapeHtml(question));
  const pending = addMessage("assistant", "Retrieving…");
  trimChatHistory();
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
  });
  const data = await res.json();
  pending.querySelector(".bubble").innerHTML = escapeHtml(
    data.answer || data.detail || "No answer"
  );
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  ask(q);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-q]").forEach((btn) => {
  btn.addEventListener("click", () => ask(btn.dataset.q));
});

document.getElementById("clear-chat").addEventListener("click", () => {
  thread.replaceChildren();
  input.value = "";
  input.focus();
});

document.getElementById("doc-search").addEventListener("input", renderSources);
document.getElementById("doc-sort").addEventListener("change", renderSources);
docsMore.addEventListener("click", () => {
  docsExpanded = !docsExpanded;
  renderSources();
  if (!docsExpanded) sourceList.scrollTop = 0;
});

document.getElementById("reindex").addEventListener("click", async () => {
  ingestStatus.textContent = "Indexing…";
  const res = await fetch("/api/ingest", { method: "POST" });
  const data = await res.json();
  ingestStatus.textContent = data.ok ? `Indexed ${data.chunks} chunks` : data.detail || "Failed";
  refreshSources();
});

document.getElementById("url-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = document.getElementById("url-input").value.trim();
  if (!url) return;
  ingestStatus.textContent = "Fetching URL…";
  const res = await fetch("/api/ingest/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const data = await res.json();
  ingestStatus.textContent = data.ok ? `Indexed ${data.chunks} chunks` : data.detail || "Failed";
  document.getElementById("url-input").value = "";
  refreshSources();
});

async function uploadFiles(files) {
  for (const file of files) {
    ingestStatus.textContent = `Uploading ${file.name}…`;
    const body = new FormData();
    body.append("file", file);
    const res = await fetch("/api/ingest/upload", { method: "POST", body });
    const data = await res.json();
    ingestStatus.textContent = data.ok ? `Added ${data.file}` : data.detail || "Failed";
    if (!data.ok) return;
  }
  refreshSources();
}

fileInput.addEventListener("change", async (e) => {
  const files = [...e.target.files];
  if (!files.length) return;
  await uploadFiles(files);
  fileInput.value = "";
});

["dragenter", "dragover"].forEach((ev) => {
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag");
  });
});
["dragleave", "drop"].forEach((ev) => {
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag");
  });
});
dropzone.addEventListener("drop", (e) => {
  const files = [...e.dataTransfer.files];
  if (files.length) uploadFiles(files);
});

sourceList.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const source = btn.getAttribute("data-del");
  if (!confirm(`Remove ${source}?`)) return;
  const res = await fetch("/api/sources/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  const data = await res.json();
  ingestStatus.textContent = data.ok ? "Removed" : data.detail || "Failed";
  refreshSources();
});

document.getElementById("how-btn").addEventListener("click", () => {
  document.getElementById("how-dialog").showModal();
});
document.getElementById("settings-btn").addEventListener("click", () => {
  document.getElementById("settings-dialog").showModal();
});
document.getElementById("settings-cancel").addEventListener("click", () => {
  document.getElementById("settings-dialog").close();
});
document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const key = document.getElementById("api-key-input").value.trim();
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ openai_api_key: key }),
  });
  const data = await res.json();
  hasLlm = Boolean(data.llm);
  if (hasLlm) modeSelect.value = "openai";
  document.getElementById("settings-dialog").close();
  ingestStatus.textContent = hasLlm ? "OpenAI key saved" : "Key cleared — using extractive answers";
});

modeSelect.addEventListener("change", () => {
  if (modeSelect.value === "openai" && !hasLlm) {
    document.getElementById("settings-dialog").showModal();
  }
  if (modeSelect.value === "huggingface" && !hasHuggingFace) {
    ingestStatus.textContent = "Hugging Face models are still being prepared.";
  }
});

refreshSources().catch((err) => {
  ingestStatus.textContent = String(err);
});

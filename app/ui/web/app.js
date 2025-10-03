// ========================= AUTH GUARD =========================
(function () {
  const PUBLIC = new Set(["/auth.html", "/favicon.ico"]);
  const token = localStorage.getItem("sec_token");
  if (!token && !PUBLIC.has(location.pathname)) {
    location.replace("/auth.html");
  }
})();

const TOKEN_KEY = "sec_token";
function authHeaders() {
  const t = localStorage.getItem(TOKEN_KEY);
  return {
    "Content-Type": "application/json",
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
  };
}

// ======================= DOM refs =======================
const $ = (s) => document.querySelector(s);
const messagesEl = $("#messages");
const promptEl = $("#prompt");
const sendBtn = $("#send");
const newChatBtn = $("#newChatBtn");
const searchInput = $("#searchChats");
const historyList = $("#historyList");
const foldersList = $("#foldersList");
const newFolderInp = $("#newFolderName");
const addFolderBtn = $("#addFolderBtn");
const convTitleEl = $("#convTitle");
const tracePanel = $("#tracePanel");
const traceStepsEl = $("#traceSteps");
const toggleTrace = $("#toggleTrace");
const plusBtn = $("#plusBtn");
const plusMenu = $("#plusMenu");
const typingNotice = $("#typingNotice");

// ======================= State & storage =======================
const storage = {
  load() {
    try {
      return JSON.parse(localStorage.getItem("sec_copilot_state") || "{}");
    } catch {
      return {};
    }
  },
  save(s) {
    localStorage.setItem("sec_copilot_state", JSON.stringify(s));
  },
};

let state = Object.assign(
  {
    conversations: {}, // id -> { id, title, messages:[{role,content,html}], final, steps }
    order: [], // newest first ids
    folders: {}, // id -> { id, name, chatIds:[] }
    folderOrder: [], // newest first ids
  },
  storage.load()
);

let activeId = null;

// ======================= Helpers =======================
function showTyping(show) {
  if (!typingNotice) return;
  typingNotice.classList.toggle("hidden", !show);
}

function bubble(role, html) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const badgeDot =
    role === "assistant"
      ? "dot-assistant"
      : role === "user"
      ? "dot-user"
      : "dot-system";
  const label =
    role === "assistant" ? "SEC-COPILOT" : role === "user" ? "You" : "System";

  wrap.innerHTML = `
    <div class="avatar">${
      role === "assistant" ? "🛡️" : role === "user" ? "🧑" : "⚙️"
    }</div>
    <div class="bubble chat-bubble ${
      role === "assistant"
        ? "bubble-assistant"
        : role === "user"
        ? "bubble-user"
        : ""
    }">
      <div class="role-badge"><span class="role-dot ${badgeDot}"></span>${label}</div>
      <div class="content" style="margin-top:6px">${html}</div>
    </div>
  `;
  return wrap;
}

function typingBubble() {
  const el = document.createElement("div");
  el.className = "msg assistant";
  el.innerHTML = `
    <div class="avatar">🛡️</div>
    <div class="bubble typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
  `;
  return el;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// small util
function debounce(fn, ms = 120) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// ======================= API wrapper =======================
async function api(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: { ...(opts.headers || {}), ...authHeaders() },
  });

  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    location.replace("/auth.html");
    throw { detail: "Unauthorized" };
  }

  if (!res.ok) {
    // Try JSON; fall back to text; fall back to statusText
    let err;
    try {
      err = await res.json();
    } catch {
      const text = await res.text().catch(() => "");
      err = { detail: text || res.statusText };
    }
    throw err;
  }

  if (res.status === 204) return null; // not used now, but harmless
  return res.json();
}

// ======================= Data fetchers =======================
async function loadFolders() {
  const folders = await api("/data/folders");
  state.folders = {};
  state.folderOrder = [];
  folders.forEach((f) => {
    state.folders[f.id] = { ...f, chatIds: f.chatIds || [] };
    state.folderOrder.unshift(f.id);
  });
}

async function loadHistory() {
  const list = await api("/data/conversations");
  state.conversations = {};
  state.order = [];
  list.forEach((c) => {
    state.conversations[c.id] = { ...c, messages: [] };
    state.order.push(c.id);
  });
  state.order.sort((a, b) =>
    (state.conversations[b].updated_at || "").localeCompare(
      state.conversations[a].updated_at || ""
    )
  );
}

async function createFolder(name) {
  const f = await api("/data/folders", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  await loadFolders();
  return f;
}

async function createConversation(title, folder_id = null) {
  const c = await api("/data/conversations", {
    method: "POST",
    body: JSON.stringify({ title, folder_id }),
  });
  await loadHistory();
  return c;
}

// ======================= Trace rendering =======================
function renderTrace(steps) {
  traceStepsEl.innerHTML = "";
  (steps || []).forEach((s) => {
    const calls = (s.tool_calls || [])
      .map((t) => `<span class="pill">${t.name}</span>`)
      .join(" ");
    const hits = (s.policy_hits || [])
      .map((h) => `<span class="pill warn">${h}</span>`)
      .join(" ");
    const div = document.createElement("div");
    div.className = "tstep";
    div.innerHTML = `
      <div class="tmeta"><div><strong>${escapeHtml(
        s.agent || "agent"
      )}</strong></div><div>conf ${(s.confidence ?? 0).toFixed(2)}</div></div>
      <div>${escapeHtml(s.rationale || "")}</div>
      ${calls ? `<div class="pills">${calls}</div>` : ""}
      ${hits ? `<div class="pills">${hits}</div>` : ""}
      ${
        s.outputs
          ? `<pre style="margin-top:6px;white-space:pre-wrap">${escapeHtml(
              JSON.stringify(s.outputs, null, 2)
            )}</pre>`
          : ""
      }
    `;
    traceStepsEl.appendChild(div);
  });
}

// Convert FinalDecision to HTML
function renderSolution(final) {
  if (!final) return "No decision.";
  const steps = Array.isArray(final.recommendations)
    ? final.recommendations
    : [];
  const list = steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  return `<div><strong>${escapeHtml(final.summary || "")}</strong></div>
          <div style="color:#6b7280;font-size:13px;margin:6px 0">Risk score: ${(
            final.risk_score ?? 0
          ).toFixed(2)}</div>
          ${steps.length ? `<ol>${list}</ol>` : ""}`;
}

// Same, but plain text (for typewriter)
function solutionPlainText(final) {
  if (!final) return "No decision.";
  const parts = [];
  if (final.summary) parts.push(final.summary);
  if (Array.isArray(final.recommendations) && final.recommendations.length) {
    final.recommendations.forEach((s, i) => parts.push(`${i + 1}. ${s}`));
  }
  if (typeof final.risk_score === "number") {
    parts.push(`Risk score: ${final.risk_score.toFixed(2)}`);
  }
  return parts.join("\n\n");
}

// ======================= Sidebar: folders & history =======================
function redrawFolders() {
  if (!foldersList) return;
  foldersList.innerHTML = "";
  state.folderOrder.forEach((fid) => {
    const f = state.folders[fid];
    if (!f) return;
    const li = document.createElement("li");
    li.className = "folder";
    li.innerHTML = `
      <div class="folder-head" data-fid="${fid}">
        <div class="folder-title">📁 ${escapeHtml(f.name)}</div>
        <div class="tiny muted">${(f.chatIds || []).length} chats</div>
      </div>
      <div class="folder-body hidden"><ul class="folder-chats"></ul></div>
    `;
    const body = li.querySelector(".folder-body");
    const list = li.querySelector(".folder-chats");
    (f.chatIds || []).forEach((cid) => {
      const c = state.conversations[cid];
      if (!c) return;
      const item = document.createElement("li");
      item.innerHTML = `<button class="chat-link" data-id="${cid}">
          <span>${escapeHtml(c.title || "Untitled")}</span>
          <span class="tiny">${new Date(
            c.time || Date.now()
          ).toLocaleDateString()}</span>
        </button>`;
      list.appendChild(item);
    });
    li.querySelector(".folder-head").addEventListener("click", () => {
      body.classList.toggle("hidden");
    });
    foldersList.appendChild(li);
  });
}

function redrawHistory(filter = "") {
  if (!historyList) return;
  historyList.innerHTML = "";
  state.order.forEach((id) => {
    const c = state.conversations[id];
    if (!c) return;
    if (filter && !(c.title || "").toLowerCase().includes(filter.toLowerCase()))
      return;
    const li = document.createElement("li");
    li.innerHTML = `<button class="chat-link" data-id="${id}">
        <span>${escapeHtml(c.title || "Untitled")}</span>
        <span class="tiny">${new Date(
          c.time || Date.now()
        ).toLocaleDateString()}</span>
      </button>`;
    historyList.appendChild(li);
  });
}

function attachHistoryEvents() {
  historyList?.querySelectorAll(".chat-link").forEach((btn) => {
    btn.addEventListener("click", () => openConversation(btn.dataset.id));
  });
  foldersList?.querySelectorAll(".chat-link").forEach((btn) => {
    btn.addEventListener("click", () => openConversation(btn.dataset.id));
  });
}

// ======================= Conversation ops =======================
async function newConversation(folderId = null) {
  // 1) create on server
  const conv = await createConversation("New conversation", folderId);

  // 2) set active
  activeId = conv.id;

  // 3) ensure local cache has this conversation
  state.conversations[conv.id] = {
    ...(state.conversations[conv.id] || {}),
    id: conv.id,
    title: conv.title || "New conversation",
    messages: [],
    steps: null,
    final: null,
    updated_at: conv.updated_at || new Date().toISOString(),
    time: Date.now(),
  };

  // 4) put it at the top of the order if it’s not already present
  if (!state.order.includes(conv.id)) {
    state.order.unshift(conv.id);
  }

  // 5) render the fresh chat page intro (does NOT erase other convs)
  convTitleEl && (convTitleEl.textContent = "New conversation");
  if (messagesEl) {
    messagesEl.innerHTML = `
      <div class="msg assistant intro">
        <div class="avatar">🛡️</div>
        <div class="bubble"><div class="content">
          New chat. Ask me anything about your investigation.
        </div></div>
      </div>`;
  }

  // 6) reset trace panel
  if (traceStepsEl) traceStepsEl.innerHTML = "";
  tracePanel?.classList.add("hidden");
  if (toggleTrace) toggleTrace.textContent = "Show agent trace";

  // 7) update sidebars
  redrawHistory();
  redrawFolders();
  attachHistoryEvents();

  // 8) persist AFTER all local state changes
  storage.save(state);

  // 9) refresh history from server quietly
  loadHistory()
    .then(() => {
      redrawHistory();
      redrawFolders();
      attachHistoryEvents();
      storage.save(state);
    })
    .catch(() => {});

  promptEl?.focus();
}

function openConversation(id) {
  const c = state.conversations[id];
  if (!c) return;
  activeId = id;
  if (convTitleEl) convTitleEl.textContent = c.title || "Conversation";
  if (messagesEl) {
    messagesEl.innerHTML = "";
    (c.messages || []).forEach((m) =>
      messagesEl.appendChild(bubble(m.role, m.html))
    );
  }
  scrollToBottom();
  renderTrace(c.steps || []);
  tracePanel?.classList.add("hidden");
  if (toggleTrace) toggleTrace.textContent = "Show agent trace";
  showTyping(false);
}

// ======================= Typewriter =======================
function typewriterInto(el, fullText, speed = 12) {
  return new Promise((resolve) => {
    let i = 0;
    const safe = String(fullText || "");
    el.textContent = "";
    const handle = setInterval(() => {
      i += Math.max(1, Math.round(safe.length / 60));
      el.textContent = safe.slice(0, i);
      if (i >= safe.length) {
        clearInterval(handle);
        resolve();
      }
    }, speed);
  });
}

// ======================= Send flow =======================
async function sendPrompt() {
  const text = (promptEl?.value || "").trim();
  if (!text) return;

  if (!activeId) await newConversation();

  const c = state.conversations[activeId];

  // user bubble
  const userHtml = escapeHtml(text);
  const userNode = bubble("user", userHtml);
  messagesEl?.appendChild(userNode);
  c.messages.push({ role: "user", html: userHtml, content: text });
  if (c.title === "New conversation") c.title = text.slice(0, 60);
  if (convTitleEl) convTitleEl.textContent = c.title;
  if (promptEl) {
    promptEl.value = "";
    promptEl.focus();
  }
  scrollToBottom();

  // assistant placeholder + typing indicator
  const asstNode = bubble("assistant", "");
  const contentTarget = asstNode.querySelector(".content");
  messagesEl?.appendChild(asstNode);
  showTyping(true);
  scrollToBottom();
  if (sendBtn) sendBtn.disabled = true;

  try {
    const body = {
      messages: [{ role: "user", content: text }],
      mode: "assist",
      conversation_id: activeId,
    };
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });

    // typewriter on plain text for smooth animation
    const plain = solutionPlainText(data.final);
    await typewriterInto(contentTarget, plain, 8);

    // swap to rich HTML at the end
    contentTarget.innerHTML = renderSolution(data.final);

    // persist in state
    const ansHtml = contentTarget.innerHTML;
    c.messages.push({
      role: "assistant",
      html: ansHtml,
      content: data.final?.summary || "",
    });
    c.final = data.final;
    c.steps = data.steps;
    c.time = Date.now();
    renderTrace(c.steps);

    state.order = [activeId, ...state.order.filter((id) => id !== activeId)];
    storage.save(state);
    redrawHistory(searchInput?.value.trim() || "");
    redrawFolders();
    attachHistoryEvents();
    scrollToBottom();
  } catch (err) {
    console.error(err);
    contentTarget.textContent = "Something went wrong. Please try again.";
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    showTyping(false);
  }
}

// ======================= Events =======================
// composer submit
$("#composer")?.addEventListener("submit", (e) => {
  e.preventDefault();
  sendPrompt();
});
sendBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  sendPrompt();
});

// new chat
newChatBtn?.addEventListener("click", () => newConversation());

// history search (debounced)
searchInput?.addEventListener(
  "input",
  debounce(() => {
    redrawHistory(searchInput.value.trim());
    attachHistoryEvents();
  })
);

// trace panel
toggleTrace?.addEventListener("click", () => {
  const nowHidden = tracePanel.classList.toggle("hidden");
  toggleTrace.textContent = nowHidden ? "Show agent trace" : "Hide agent trace";
});

// plus menu (guard for pages without it)
if (plusBtn && plusMenu) {
  plusBtn.addEventListener("click", () => plusMenu.classList.toggle("hidden"));
  document.addEventListener("click", (e) => {
    if (!plusMenu.contains(e.target) && e.target !== plusBtn)
      plusMenu.classList.add("hidden");
  });
  plusMenu.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") return;
    const k = e.target.dataset.menu;
    if (k === "agent") toggleTrace?.click();
    else alert(`${e.target.textContent} — placeholder action (wire later)`);
  });
}

// folders
addFolderBtn?.addEventListener("click", async () => {
  const name = (newFolderInp?.value || "").trim();
  if (!name) return;
  await createFolder(name);
  if (newFolderInp) newFolderInp.value = "";
  redrawFolders();
  attachHistoryEvents();
});

// quick move
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key?.toLowerCase() === "m") {
    if (!activeId) return alert("Open a chat first.");
    const names = state.folderOrder.map((fid) => state.folders[fid].name);
    const which = prompt(
      `Move to which project?\n${names
        .map((n, i) => `${i + 1}. ${n}`)
        .join("\n")}`
    );
    const idx = parseInt(which || "", 10) - 1;
    if (Number.isNaN(idx) || idx < 0 || idx >= state.folderOrder.length) return;
    const fid = state.folderOrder[idx];
    Object.values(state.folders).forEach((f) => {
      f.chatIds = (f.chatIds || []).filter((id) => id !== activeId);
    });
    (state.folders[fid].chatIds ||= []).unshift(activeId);
    storage.save(state);
    redrawFolders();
    attachHistoryEvents();
  }
});

// ======================= Boot =======================
async function boot() {
  try {
    await loadFolders();
    await loadHistory();
  } catch (e) {
    console.error(e);
    localStorage.removeItem(TOKEN_KEY);
    location.replace("/auth.html");
    return;
  }
  redrawHistory();
  redrawFolders();
  attachHistoryEvents();
  if (state.order.length === 0) {
    await newConversation();
  } else {
    openConversation(state.order[0]);
    // refresh sidebar from server to ensure everything matches DB
    loadHistory()
      .then(() => {
        redrawHistory();
        redrawFolders();
        attachHistoryEvents();
        storage.save(state);
      })
      .catch(() => {});
  }
}
boot();

// Mobile sidebar wiring
const sidebar = document.getElementById("sidebar");
const backdrop = document.getElementById("backdrop");
const openBtn = document.getElementById("openSidebar");
const closeBtn = document.getElementById("closeSidebar");

function openSidebar() {
  sidebar?.classList.add("open");
  backdrop?.classList.remove("hidden");
}
function closeSidebar() {
  sidebar?.classList.remove("open");
  backdrop?.classList.add("hidden");
}

openBtn?.addEventListener("click", openSidebar);
closeBtn?.addEventListener("click", closeSidebar);
backdrop?.addEventListener("click", closeSidebar);

// Logout
document.getElementById("logoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  window.location.replace("/auth.html");
});

/* ================= THEME MANAGER ================= */
(function () {
  const THEME_KEY = "sec_theme";
  const root = document.documentElement;
  const mql = window.matchMedia
    ? window.matchMedia("(prefers-color-scheme: dark)")
    : null;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    const cb = document.getElementById("dn");
    if (cb) cb.checked = theme === "dark";
  }

  function detectSystem() {
    return mql && mql.matches ? "dark" : "light";
  }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    applyTheme(saved || detectSystem());

    // If user hasn't overridden, keep following system changes
    if (!saved && mql) {
      try {
        mql.addEventListener("change", (e) =>
          applyTheme(e.matches ? "dark" : "light")
        );
      } catch {
        // Safari fallback
        mql.addListener &&
          mql.addListener((e) => applyTheme(e.matches ? "dark" : "light"));
      }
    }

    // Hook the toggle
    const cb = document.getElementById("dn");
    if (cb) {
      cb.addEventListener("change", () => {
        const chosen = cb.checked ? "dark" : "light";
        localStorage.setItem(THEME_KEY, chosen);
        applyTheme(chosen);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTheme);
  } else {
    initTheme();
  }
})();

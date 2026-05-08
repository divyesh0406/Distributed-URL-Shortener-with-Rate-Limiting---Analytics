const DEFAULT_API_URL = "https://distributed-url-shortener-with-rate.onrender.com";

const els = {
  form: document.querySelector("#shorten-form"),
  longUrl: document.querySelector("#long-url"),
  idempotencyKey: document.querySelector("#idempotency-key"),
  shortUrl: document.querySelector("#short-url"),
  resultTitle: document.querySelector("#result-title"),
  total: document.querySelector("#metric-total"),
  last24h: document.querySelector("#metric-24h"),
  last7d: document.querySelector("#metric-7d"),
  copy: document.querySelector("#copy-button"),
  open: document.querySelector("#open-button"),
  analytics: document.querySelector("#analytics-button"),
  reset: document.querySelector("#reset-button"),
  apiUrl: document.querySelector("#api-url"),
  statusDot: document.querySelector("#status-dot"),
  statusText: document.querySelector("#status-text"),
  urlList: document.querySelector("#url-list"),
  listCount: document.querySelector("#list-count"),
  toast: document.querySelector("#toast"),
  resultPanel: document.querySelector(".result-panel"),
};

let currentCode = "";
let currentShortUrl = "";

function apiBase() {
  return els.apiUrl.value.replace(/\/$/, "");
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.setTimeout(() => els.toast.classList.remove("show"), 2200);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const data =
    response.status === 204
      ? null
      : contentType.includes("application/json")
        ? await response.json()
        : await response.text();

  if (!response.ok) {
    const detail = typeof data === "object" ? data.detail : data;
    throw new Error(Array.isArray(detail) ? detail[0]?.msg : detail || "Request failed");
  }

  return data;
}

async function checkHealth() {
  try {
    await request("/health");
    els.statusDot.classList.add("ok");
    els.statusText.textContent = "Online";
  } catch {
    els.statusDot.classList.remove("ok");
    els.statusText.textContent = "Unavailable";
  }
}

function setResult(data) {
  currentCode = data.short_code;
  currentShortUrl = data.short_url;
  els.shortUrl.value = data.short_url;
  els.resultTitle.textContent = data.short_code;
  els.open.disabled = false;
  els.analytics.disabled = false;
  highlightSelectedRow();
}

function highlightSelectedRow() {
  document.querySelectorAll(".url-item").forEach((row) => {
    row.classList.toggle("selected", row.dataset.code === currentCode);
  });
}

function renderAllLinks(items) {
  els.listCount.textContent = items.length;

  if (items.length === 0) {
    els.urlList.innerHTML = '<p class="empty-state">No short links yet.</p>';
    return;
  }

  els.urlList.innerHTML = items
    .map(
      (item) => `
        <article class="url-item" data-code="${escapeHtml(item.short_code)}" data-short-url="${escapeHtml(item.short_url)}">
          <div class="url-main">
            <p class="url-code">${escapeHtml(item.short_code)}</p>
            <span class="url-short">${escapeHtml(item.short_url)}</span>
            <span class="url-long">${escapeHtml(item.long_url)}</span>
            <div class="url-stats">
              <span>Total ${escapeHtml(item.total_clicks)}</span>
              <span>24h ${escapeHtml(item.clicks_last_24h)}</span>
              <span>7d ${escapeHtml(item.clicks_last_7d)}</span>
            </div>
          </div>
          <div class="url-actions">
            <button class="mini-button" type="button" data-action="select" title="Show this URL in the Result panel">View</button>
            <button class="mini-button" type="button" data-action="copy">Copy</button>
            <button class="mini-button" type="button" data-action="open">Open</button>
            <button class="mini-button danger-button" type="button" data-action="delete">Delete</button>
          </div>
        </article>
      `,
    )
    .join("");
  highlightSelectedRow();
}

async function refreshAnalytics() {
  if (!currentCode) return;

  const data = await request(`/analytics/${currentCode}`);
  els.total.textContent = data.total_clicks;
  els.last24h.textContent = data.clicks_last_24h;
  els.last7d.textContent = data.clicks_last_7d;
}

async function refreshAllResults() {
  const items = await request("/analytics");
  renderAllLinks(items);
}

async function refreshAllResultsQuietly() {
  try {
    await refreshAllResults();
  } catch {
    showToast("All results need the latest backend. Rebuild or redeploy the API.");
  }
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    long_url: els.longUrl.value,
  };

  if (els.idempotencyKey.value.trim()) {
    payload.idempotency_key = els.idempotencyKey.value.trim();
  }

  try {
    const data = await request("/shorten", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setResult(data);
    await refreshAnalytics();
    await refreshAllResultsQuietly();
    showToast("Short link created");
  } catch (error) {
    showToast(error.message);
  }
});

els.copy.addEventListener("click", async () => {
  if (!currentShortUrl) return;
  await navigator.clipboard.writeText(currentShortUrl);
  showToast("Copied");
});

els.open.addEventListener("click", () => {
  if (currentShortUrl) {
    window.open(currentShortUrl, "_blank", "noopener,noreferrer");
  }
});

els.analytics.addEventListener("click", async () => {
  try {
    await refreshAnalytics();
    await refreshAllResultsQuietly();
    showToast("Analytics refreshed");
  } catch (error) {
    showToast(error.message);
  }
});

els.urlList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  const item = event.target.closest(".url-item");

  if (!button || !item) return;

  const action = button.dataset.action;
  const shortCode = item.dataset.code;
  const shortUrl = item.dataset.shortUrl;

  if (action === "copy") {
    await navigator.clipboard.writeText(shortUrl);
    showToast("Copied");
    return;
  }

  if (action === "open") {
    window.open(shortUrl, "_blank", "noopener,noreferrer");
    return;
  }

  if (action === "select") {
    currentCode = shortCode;
    currentShortUrl = shortUrl;
    els.shortUrl.value = shortUrl;
    els.resultTitle.textContent = shortCode;
    els.open.disabled = false;
    els.analytics.disabled = false;
    await refreshAnalytics();
    highlightSelectedRow();
    els.resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    showToast("Loaded in Result panel");
    return;
  }

  if (action === "delete") {
    const confirmed = window.confirm(`Delete short URL ${shortCode}?`);
    if (!confirmed) return;

    try {
      try {
        await request(`/urls/${shortCode}`, { method: "DELETE" });
      } catch (error) {
        if (!error.message.includes("not found")) {
          throw error;
        }
        await request(`/analytics/${shortCode}`, { method: "DELETE" });
      }

      if (currentCode === shortCode) {
        currentCode = "";
        currentShortUrl = "";
        els.shortUrl.value = "";
        els.resultTitle.textContent = "Ready";
        els.total.textContent = "0";
        els.last24h.textContent = "0";
        els.last7d.textContent = "0";
        els.open.disabled = true;
        els.analytics.disabled = true;
      }

      await refreshAllResultsQuietly();
      showToast("Deleted");
    } catch (error) {
      showToast(error.message);
    }
  }
});

els.reset.addEventListener("click", () => {
  els.form.reset();
  currentCode = "";
  currentShortUrl = "";
  els.shortUrl.value = "";
  els.resultTitle.textContent = "Ready";
  els.total.textContent = "0";
  els.last24h.textContent = "0";
  els.last7d.textContent = "0";
  els.open.disabled = true;
  els.analytics.disabled = true;
});

els.apiUrl.addEventListener("change", () => {
  localStorage.setItem("apiUrl", apiBase());
  checkHealth();
  refreshAllResultsQuietly();
});

els.apiUrl.value = localStorage.getItem("apiUrl") || DEFAULT_API_URL;
checkHealth();
refreshAllResultsQuietly();

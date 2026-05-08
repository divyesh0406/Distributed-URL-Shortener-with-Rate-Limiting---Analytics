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
  toast: document.querySelector("#toast"),
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

async function request(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
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
}

async function refreshAnalytics() {
  if (!currentCode) return;

  const data = await request(`/analytics/${currentCode}`);
  els.total.textContent = data.total_clicks;
  els.last24h.textContent = data.clicks_last_24h;
  els.last7d.textContent = data.clicks_last_7d;
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
    showToast("Analytics refreshed");
  } catch (error) {
    showToast(error.message);
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
});

els.apiUrl.value = localStorage.getItem("apiUrl") || DEFAULT_API_URL;
checkHealth();

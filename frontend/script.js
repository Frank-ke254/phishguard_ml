const form = document.getElementById("predict-form");
const urlInput = document.getElementById("url-input");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const urlErrorEl = document.getElementById("url-error");
const batchForm = document.getElementById("batch-form");
const batchInput = document.getElementById("batch-input");
const batchErrorEl = document.getElementById("batch-error");
const batchSubmitBtn = document.getElementById("batch-submit-btn");
const downloadBtn = document.getElementById("download-btn");
const resultCard = document.getElementById("result-card");
const resultUrl = document.getElementById("result-url");
const resultPrediction = document.getElementById("result-prediction");
const resultConfidence = document.getElementById("result-confidence");
const resultLabel = document.getElementById("result-label");
const resultAction = document.getElementById("result-action");
const resultRiskBadge = document.getElementById("result-risk-badge");
const riskFlags = document.getElementById("risk-flags");
const confidenceFill = document.getElementById("confidence-fill");
const historyList = document.getElementById("history-list");
const batchSummary = document.getElementById("batch-summary");
const sumTotal = document.getElementById("sum-total");
const sumPhishing = document.getElementById("sum-phishing");
const sumSafe = document.getElementById("sum-safe");
const sumHighRisk = document.getElementById("sum-high-risk");
const topRiskyBody = document.getElementById("top-risky-body");

const HISTORY_KEY = "phishguardRecentPredictions";
const HISTORY_LIMIT = 8;
let lastBatchResults = [];

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b42318" : "#2f4858";
}

function setUrlError(message = "") {
  if (!message) {
    urlErrorEl.textContent = "";
    urlErrorEl.classList.add("hidden");
    return;
  }
  urlErrorEl.textContent = message;
  urlErrorEl.classList.remove("hidden");
}

function setBatchError(message = "") {
  if (!message) {
    batchErrorEl.textContent = "";
    batchErrorEl.classList.add("hidden");
    return;
  }
  batchErrorEl.textContent = message;
  batchErrorEl.classList.remove("hidden");
}

function getHistory() {
  try {
    const saved = localStorage.getItem(HISTORY_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveHistory(items) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, HISTORY_LIMIT)));
}

function renderHistory() {
  const items = getHistory();
  if (!items.length) {
    historyList.innerHTML = "<li class='history-item'>No predictions yet.</li>";
    return;
  }

  historyList.innerHTML = items
    .map(
      (item) =>
        `<li class="history-item">
          <span title="${item.url}">${item.url}</span>
          <span class="tag ${item.prediction}">${item.prediction.toUpperCase()} (${item.confidence}%)</span>
        </li>`
    )
    .join("");
}

function addHistoryItem(data) {
  const current = getHistory();
  const next = [
    {
      url: data.url,
      prediction: data.prediction,
      confidence: (Number(data.confidence) * 100).toFixed(2),
    },
    ...current,
  ];
  saveHistory(next);
  renderHistory();
}

function getRiskLevel(prediction, confidencePct) {
  if (prediction === "phishing" && confidencePct >= 80) {
    return "High";
  }
  if (prediction === "phishing" || confidencePct >= 60) {
    return "Medium";
  }
  return "Low";
}

function riskClassFromLevel(level) {
  return level.toLowerCase();
}

function renderResult(data) {
  const confidencePct = Number(data.confidence) * 100;
  const riskLevel = getRiskLevel(data.prediction, confidencePct);
  resultUrl.textContent = data.url;
  resultPrediction.textContent = data.prediction;
  resultConfidence.textContent = `${confidencePct.toFixed(2)}%`;
  resultLabel.textContent = String(data.label);
  resultAction.textContent = data.recommended_action || "-";
  resultRiskBadge.textContent = riskLevel;
  resultRiskBadge.className = `risk-badge ${riskClassFromLevel(riskLevel)}`;
  confidenceFill.style.width = `${Math.max(0, Math.min(confidencePct, 100))}%`;
  const flags = Array.isArray(data.risk_flags) ? data.risk_flags : [];
  riskFlags.innerHTML = flags.length
    ? flags.map((flag) => `<li>${flag}</li>`).join("")
    : "<li>No obvious lexical risk flags detected.</li>";

  resultCard.classList.remove("hidden", "safe", "phishing");
  resultCard.classList.add(data.prediction === "phishing" ? "phishing" : "safe");
}

function parseBulkInput(raw) {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function renderBatchSummary(data) {
  batchSummary.classList.remove("hidden");
  sumTotal.textContent = String(data.total);
  sumPhishing.textContent = String(data.phishing_count);
  sumSafe.textContent = String(data.safe_count);
  sumHighRisk.textContent = String(data.high_risk_count);
  renderTopRiskyTable(data.results || []);
}

function renderTopRiskyTable(results) {
  const sorted = [...results]
    .sort((a, b) => Number(b.confidence) - Number(a.confidence))
    .slice(0, 8);

  if (!sorted.length) {
    topRiskyBody.innerHTML = "<tr><td colspan='4'>No batch results yet.</td></tr>";
    return;
  }

  topRiskyBody.innerHTML = sorted
    .map((item) => {
      const confidencePct = Number(item.confidence) * 100;
      const level = getRiskLevel(item.prediction, confidencePct);
      return `<tr>
        <td class="risk-url" title="${item.url}">${item.url}</td>
        <td>${item.prediction}</td>
        <td>${confidencePct.toFixed(2)}%</td>
        <td><span class="risk-badge ${riskClassFromLevel(level)}">${level}</span></td>
      </tr>`;
    })
    .join("");
}

function toCsvRows(items) {
  const header = ["url", "prediction", "label", "confidence", "recommended_action", "risk_flags"];
  const rows = items.map((item) => [
    item.url,
    item.prediction,
    item.label,
    item.confidence,
    item.recommended_action || "",
    Array.isArray(item.risk_flags) ? item.risk_flags.join(" | ") : "",
  ]);
  return [header, ...rows];
}

function csvEscapeCell(value) {
  const raw = String(value ?? "");
  return `"${raw.replace(/"/g, '""')}"`;
}

function buildCsv(rows) {
  return rows.map((row) => row.map(csvEscapeCell).join(",")).join("\n");
}

function downloadCsv(filename, content) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

renderHistory();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = urlInput.value.trim();
  setUrlError();

  if (!url) {
    setStatus("Please enter a valid URL.", true);
    setUrlError("URL is required.");
    return;
  }

  setStatus("Analyzing URL...");
  submitBtn.disabled = true;
  resultCard.classList.add("hidden");

  try {
    const response = await fetch("/api/predict/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();
    if (!response.ok) {
      const detail = data?.error?.message || "Prediction failed.";
      if (data?.error?.fields?.url) {
        setUrlError(data.error.fields.url);
      }
      throw new Error(detail);
    }

    renderResult(data);
    addHistoryItem(data);
    setStatus("Prediction completed.");
  } catch (error) {
    setStatus(error.message || "Unable to reach API.", true);
  } finally {
    submitBtn.disabled = false;
  }
});

batchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBatchError();
  batchSummary.classList.add("hidden");

  const urls = parseBulkInput(batchInput.value);
  if (!urls.length) {
    setBatchError("Please provide at least one URL.");
    setStatus("Bulk scan requires URL input.", true);
    return;
  }
  if (urls.length > 200) {
    setBatchError("Maximum 200 URLs per batch.");
    setStatus("Reduce input size and try again.", true);
    return;
  }

  setStatus("Running bulk scan...");
  batchSubmitBtn.disabled = true;
  downloadBtn.disabled = true;

  try {
    const response = await fetch("/api/batch-predict/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls }),
    });

    const data = await response.json();
    if (!response.ok) {
      const detail = data?.error?.message || "Bulk scan failed.";
      if (data?.error?.fields?.urls) {
        setBatchError(data.error.fields.urls);
      }
      throw new Error(detail);
    }

    renderBatchSummary(data);
    lastBatchResults = data.results || [];
    downloadBtn.disabled = !lastBatchResults.length;
    setStatus(`Bulk scan complete. ${data.phishing_count} phishing URLs detected.`);
  } catch (error) {
    setStatus(error.message || "Unable to reach API.", true);
  } finally {
    batchSubmitBtn.disabled = false;
  }
});

downloadBtn.addEventListener("click", () => {
  if (!lastBatchResults.length) {
    return;
  }
  const csvRows = toCsvRows(lastBatchResults);
  const csvText = buildCsv(csvRows);
  downloadCsv("phishguard_batch_results.csv", csvText);
});

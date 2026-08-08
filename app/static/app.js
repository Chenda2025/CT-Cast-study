const $ = (id) => document.getElementById(id);

const state = {
  polling: null,
};

const chartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  layout: { padding: { top: 4, right: 6, bottom: 2, left: 2 } },
  scales: {
    x: { display: false },
    y: {
      beginAtZero: true,
      ticks: {
        color: "#9bb5a8",
        maxTicksLimit: 5,
        font: { size: 10 },
      },
      grid: { color: "rgba(62,207,142,0.12)" },
    },
  },
  plugins: {
    legend: {
      display: false,
    },
  },
};

function makeLine(canvasId, labelKey, color) {
  const ctx = $(canvasId).getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: t(labelKey),
          data: [],
          borderColor: color,
          backgroundColor: color + "33",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: chartOpts,
  });
  chart._labelKey = labelKey;
  return chart;
}

const cpuChart = makeLine("cpuChart", "chart.cpu", "#3ecf8e");
const diskChart = makeLine("diskChart", "chart.disk", "#f0b429");
const thrChart = makeLine("thrChart", "chart.thr", "#7ec8ff");

const balanceChart = new Chart($("balanceChart").getContext("2d"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: t("chart.cpu"),
        data: [],
        borderColor: "#3ecf8e",
        tension: 0.2,
        pointRadius: 3,
      },
      {
        label: t("chart.disk"),
        data: [],
        borderColor: "#f0b429",
        tension: 0.2,
        pointRadius: 3,
      },
    ],
  },
  options: {
    ...chartOpts,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: "#e8f2ec",
          boxWidth: 10,
          font: { size: 11 },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#9bb5a8", maxTicksLimit: 10, font: { size: 10 } },
        grid: { color: "rgba(62,207,142,0.08)" },
      },
      y: chartOpts.scales.y,
    },
  },
});

$("level").addEventListener("input", (e) => {
  $("levelVal").textContent = e.target.value;
});

function setBusy(busy) {
  ["btnDownload", "btnIngest", "btnMatrix", "btnSweep", "btnFull"].forEach((id) => {
    $(id).disabled = busy;
  });
}

function updateLive(live) {
  if (!Array.isArray(live) || !live.length) return;
  const labels = live.map((_, i) => i);
  cpuChart.data.labels = labels;
  diskChart.data.labels = labels;
  thrChart.data.labels = labels;
  cpuChart.data.datasets[0].data = live.map((p) => p.cpu_percent);
  diskChart.data.datasets[0].data = live.map((p) => p.disk_wait_percent);
  thrChart.data.datasets[0].data = live.map((p) => p.throughput_mb_s);
  cpuChart.update();
  diskChart.update();
  thrChart.update();
}

function updateTable(results) {
  const tbody = $("resultsTable").querySelector("tbody");
  tbody.innerHTML = "";
  (results || []).forEach((r) => {
    const tr = document.createElement("tr");
    const rp = (r.read_seconds || 0) + (r.process_seconds || 0);
    tr.innerHTML = `
      <td>${r.name || ""}</td>
      <td>${r.codec || ""}</td>
      <td>${r.level ?? ""}</td>
      <td>${r.fmt || ""}</td>
      <td>${r.compression_ratio ?? ""}</td>
      <td>${rp.toFixed ? rp.toFixed(3) : rp}</td>
      <td>${r.total_seconds ?? ""}</td>
      <td>${r.throughput_mb_s ?? ""}</td>
      <td>${r.avg_cpu_percent ?? ""}</td>
      <td>${r.avg_disk_wait_percent ?? ""}</td>
      <td>${r.peak_rss_mb ?? ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateBalance(results) {
  const sweep = (results || []).filter(
    (r) => (r.name || "").includes("zstd") || r.codec === "zstd"
  );
  const use = sweep.length ? sweep : results || [];
  const labels = use.map((r) =>
    r.level != null ? `L${r.level}` : r.codec || r.name
  );
  balanceChart.data.labels = labels;
  balanceChart.data.datasets[0].data = use.map((r) => r.avg_cpu_percent || 0);
  balanceChart.data.datasets[1].data = use.map((r) => r.avg_disk_wait_percent || 0);
  balanceChart.update();
}

function updateRecommend(rec) {
  if (!rec) return;
  $("recommendText").textContent = rec.message || JSON.stringify(rec);
}

document.addEventListener("langchange", () => {
  [cpuChart, diskChart, thrChart].forEach((c) => {
    c.data.datasets[0].label = t(c._labelKey);
    c.update();
  });
  balanceChart.data.datasets[0].label = t("chart.cpu");
  balanceChart.data.datasets[1].label = t("chart.disk");
  balanceChart.update();
});

async function poll() {
  try {
    const res = await fetch("/api/state");
    const data = await res.json();
    const status = data.status || "idle";
    const pill = $("statusPill");
    pill.dataset.i18n = `status.${status}`;
    pill.textContent = t(`status.${status}`);
    pill.className = `pill ${status}`;
    if (data.message) {
      $("message").removeAttribute("data-i18n");
      $("message").textContent = data.message;
    }
    if (data.error) {
      $("error").hidden = false;
      $("error").textContent = data.error;
    } else {
      $("error").hidden = true;
    }
    updateLive(data.live);
    if (data.results && data.results.length) {
      updateTable(data.results);
      updateBalance(data.results);
    }
    if (data.recommendation) updateRecommend(data.recommendation);
    setBusy(data.status === "running");
  } catch (e) {
    console.warn(e);
  }
}

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function commonBody() {
  return {
    fmt: $("fmt").value,
    codec: $("codec").value,
    level: Number($("level").value),
    threads: Number($("threads").value),
    max_rows: Number($("maxRows").value),
  };
}

$("btnDownload").onclick = async () => {
  setBusy(true);
  await post("/api/download");
};
$("btnIngest").onclick = async () => {
  setBusy(true);
  await post("/api/ingest", commonBody());
};
$("btnMatrix").onclick = async () => {
  setBusy(true);
  await post("/api/benchmark", {
    ...commonBody(),
    mode: "matrix",
    zstd_full: $("zstdFull").checked,
  });
};
$("btnSweep").onclick = async () => {
  setBusy(true);
  await post("/api/benchmark", {
    ...commonBody(),
    mode: "zstd_sweep",
    zstd_full: $("zstdFull").checked,
  });
};
$("btnFull").onclick = async () => {
  setBusy(true);
  await post("/api/benchmark", {
    ...commonBody(),
    mode: "full",
    zstd_full: $("zstdFull").checked,
  });
};

state.polling = setInterval(poll, 500);
poll();

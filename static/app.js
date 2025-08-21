const $ = (id) => document.getElementById(id);

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}

let chart;
let currentSymbol = "ETHUSDT";
let currentPeriod = "1d";
let realTimeData = [];
let historicalData = [];
let isStreaming = false;

function ensureChart() {
  if (chart) {
    chart.destroy();
  }
  const ctx = $("priceChart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Historical Data",
          data: [],
          borderColor: "#2f6fed",
          backgroundColor: "rgba(47,111,237,0.15)",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          fill: false,
          spanGaps: true, // This allows broken lines for discontinuous data
        },
        {
          label: "Real-time Data",
          data: [],
          borderColor: "#4ade80",
          backgroundColor: "rgba(74,222,128,0.15)",
          borderWidth: 3,
          pointRadius: 2,
          tension: 0.1,
          fill: false,
          spanGaps: true,
        }
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      scales: {
        x: { 
          display: true,
          type: 'time',
          time: {
            displayFormats: {
              hour: 'HH:mm',
              day: 'MMM dd',
              week: 'MMM dd',
              month: 'MMM yyyy'
            }
          }
        },
        y: { 
          display: true,
          position: 'right'
        },
      },
      plugins: { 
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
      animation: {
        duration: 0 // Disable animations for real-time updates
      }
    },
  });
  return chart;
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  if (currentPeriod === "1h") {
    return date.toLocaleTimeString();
  } else if (currentPeriod === "1d") {
    return date.toLocaleTimeString();
  } else {
    return date.toLocaleDateString();
  }
}

function updateStreamingStatus(status, message) {
  const statusEl = $("streamingStatus");
  statusEl.textContent = message;
  statusEl.className = `status-indicator ${status}`;
}

function updateChartInfo() {
  $("historicalCount").textContent = historicalData.length;
  $("realtimeCount").textContent = realTimeData.length;
  $("lastUpdate").textContent = new Date().toLocaleTimeString();
}

async function updatePrice() {
  try {
    const data = await fetchJSON(`/api/price?symbol=${encodeURIComponent(currentSymbol)}`);
    $("price").innerText = `${data.symbol}: $${Number(data.price).toFixed(2)}`;
    
    // Add to real-time data
    const timestamp = Date.now();
    realTimeData.push({
      timestamp: timestamp,
      price: Number(data.price)
    });
    
    // Keep only last 100 real-time points
    if (realTimeData.length > 100) {
      realTimeData.shift();
    }
    
    // Update chart if streaming
    if (isStreaming && chart) {
      updateChartData();
    }
    
    updateChartInfo();
  } catch (e) {
    $("price").innerText = `Error: ${e.message}`;
    updateStreamingStatus("error", "Connection Error");
  }
}

async function updateChart() {
  try {
    updateStreamingStatus("loading", "Loading Data...");
    const data = await fetchJSON(`/api/price-history?symbol=${encodeURIComponent(currentSymbol)}&period=${currentPeriod}`);
    
    if (data.data && data.data.length > 0) {
      ensureChart();
      
      // Store historical data
      historicalData = data.data.map(item => ({
        timestamp: item.timestamp,
        price: Number(item.price)
      }));
      
      // Update chart with historical data
      updateChartData();
      
      // Start real-time streaming
      if (!isStreaming) {
        isStreaming = true;
        startRealTimeStreaming();
        updateStreamingStatus("active", "Live Streaming");
      }
      
      updateChartInfo();
    } else {
      updateStreamingStatus("error", "No Data Available");
    }
  } catch (e) {
    console.error("Chart update failed:", e);
    updateStreamingStatus("error", "Load Failed");
  }
}

function updateChartData() {
  if (!chart) return;
  
  // Combine historical and real-time data
  const allData = [...historicalData, ...realTimeData];
  
  // Remove duplicates and sort by timestamp
  const uniqueData = [];
  const seen = new Set();
  
  for (const item of allData) {
    if (!seen.has(item.timestamp)) {
      seen.add(item.timestamp);
      uniqueData.push(item);
    }
  }
  
  uniqueData.sort((a, b) => a.timestamp - b.timestamp);
  
  // Separate historical and real-time data
  const historicalLabels = historicalData.map(item => new Date(item.timestamp));
  const historicalPrices = historicalData.map(item => item.price);
  
  const realTimeLabels = realTimeData.map(item => new Date(item.timestamp));
  const realTimePrices = realTimeData.map(item => item.price);
  
  // Update chart
  chart.data.labels = [...historicalLabels, ...realTimeLabels];
  chart.data.datasets[0].data = historicalPrices;
  chart.data.datasets[1].data = realTimePrices;
  chart.data.datasets[0].label = `${currentSymbol} Historical`;
  chart.data.datasets[1].label = `${currentSymbol} Real-time`;
  
  chart.update('none'); // Update without animation
}

function startRealTimeStreaming() {
  // Real-time updates are handled by updatePrice()
  // This function can be extended for WebSocket connections later
}

async function updateStatus() {
  try {
    const data = await fetchJSON("/api/status");
    $("status").innerText = JSON.stringify(data, null, 2);
    if (typeof data.dry_run === "boolean") {
      $("dryrun").checked = data.dry_run;
    }
  } catch (e) {
    $("status").innerText = `Error: ${e.message}`;
  }
}

async function startBot() {
  try {
    const buy = parseFloat($("buy").value);
    const sell = parseFloat($("sell").value);
    const qty = parseFloat($("qty").value || "0.01");
    const dryRun = $("dryrun").checked;

    const res = await fetchJSON("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        symbol: currentSymbol, 
        buy_threshold: buy, 
        sell_threshold: sell, 
        quantity: qty, 
        dry_run: dryRun 
      }),
    });
    updateStatus();
  } catch (e) {
    alert(`Start failed: ${e.message}`);
  }
}

async function stopBot() {
  try {
    await fetchJSON("/api/stop", { method: "POST" });
    updateStatus();
  } catch (e) {
    alert(`Stop failed: ${e.message}`);
  }
}

async function placeOrder() {
  try {
    const side = $("side").value;
    const qty = parseFloat($("manualQty").value || "0.01");

    const res = await fetchJSON("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: currentSymbol, side, quantity: qty }),
    });
    $("orderResult").innerText = JSON.stringify(res, null, 2);
    updateStatus();
  } catch (e) {
    $("orderResult").innerText = `Error: ${e.message}`;
  }
}

function onSymbolChange() {
  currentSymbol = $("symbolSelect").value;
  $("symbol").value = currentSymbol;
  
  // Reset data for new symbol
  realTimeData = [];
  historicalData = [];
  isStreaming = false;
  
  updateStreamingStatus("loading", "Switching Symbol...");
  updatePrice();
  updateChart();
}

function onPeriodChange() {
  currentPeriod = $("periodSelect").value;
  
  // Reset data for new period
  realTimeData = [];
  historicalData = [];
  isStreaming = false;
  
  updateStreamingStatus("loading", "Loading Period...");
  updateChart();
}

function init() {
  // Initialize chart
  ensureChart();
  
  // Set up event listeners
  $("start").addEventListener("click", startBot);
  $("stop").addEventListener("click", stopBot);
  $("order").addEventListener("click", placeOrder);
  $("symbolSelect").addEventListener("change", onSymbolChange);
  $("periodSelect").addEventListener("change", onPeriodChange);
  
  // Initial data load
  updatePrice();
  updateStatus();
  updateChart();
  
  // Set up polling
  setInterval(updatePrice, 2000);
  setInterval(updateStatus, 3000);
  setInterval(updateChart, 30000); // Chart updates less frequently for historical data
}

document.addEventListener("DOMContentLoaded", init);

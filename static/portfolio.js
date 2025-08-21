const $ = (id) => document.getElementById(id);

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}

function formatCurrency(amount) {
  if (amount === null || amount === undefined) return "-";
  const num = parseFloat(amount);
  if (isNaN(num)) return "-";
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num);
}

function formatNumber(num, decimals = 4) {
  if (num === null || num === undefined) return "-";
  const n = parseFloat(num);
  if (isNaN(n)) return "-";
  return n.toFixed(decimals);
}

function formatTimestamp(timestamp) {
  if (!timestamp) return "-";
  return new Date(timestamp).toLocaleString();
}

function updateSummaryCards(data) {
  $("totalPnl").innerText = formatCurrency(data.total_pnl);
  $("realizedPnl").innerText = formatCurrency(data.total_realized_pnl);
  $("unrealizedPnl").innerText = formatCurrency(data.total_unrealized_pnl);
  $("positionCount").innerText = data.position_count || 0;
  
  // Color coding for PnL
  const totalPnlEl = $("totalPnl");
  const unrealizedPnlEl = $("unrealizedPnl");
  
  if (data.total_pnl > 0) {
    totalPnlEl.className = "value positive";
  } else if (data.total_pnl < 0) {
    totalPnlEl.className = "value negative";
  } else {
    totalPnlEl.className = "value";
  }
  
  if (data.total_unrealized_pnl > 0) {
    unrealizedPnlEl.className = "value positive";
  } else if (data.total_unrealized_pnl < 0) {
    unrealizedPnlEl.className = "value negative";
  } else {
    unrealizedPnlEl.className = "value";
  }
}

function updatePositionsTable(positions) {
  if (!positions || positions.length === 0) {
    $("positionsTable").innerHTML = "<p>No open positions</p>";
    return;
  }
  
  const table = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Quantity</th>
          <th>Entry Price</th>
          <th>Current Price</th>
          <th>Unrealized PnL</th>
          <th>Realized PnL</th>
          <th>Entry Time</th>
        </tr>
      </thead>
      <tbody>
        ${positions.map(pos => `
          <tr>
            <td>${pos.symbol}</td>
            <td>${formatNumber(pos.quantity)}</td>
            <td>${formatCurrency(pos.entry_price)}</td>
            <td>${formatCurrency(pos.current_price)}</td>
            <td class="${pos.unrealized_pnl > 0 ? 'positive' : pos.unrealized_pnl < 0 ? 'negative' : ''}">
              ${formatCurrency(pos.unrealized_pnl)}
            </td>
            <td class="${pos.realized_pnl > 0 ? 'positive' : pos.realized_pnl < 0 ? 'negative' : ''}">
              ${formatCurrency(pos.realized_pnl)}
            </td>
            <td>${formatTimestamp(pos.entry_time)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  $("positionsTable").innerHTML = table;
}

function updateBalancesTable(balances) {
  if (!balances || balances.length === 0) {
    $("balancesTable").innerHTML = "<p>No balances found</p>";
    return;
  }
  
  const table = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Asset</th>
          <th>Free</th>
          <th>Locked</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        ${balances.map(balance => {
          const free = parseFloat(balance.free);
          const locked = parseFloat(balance.locked);
          const total = free + locked;
          return `
            <tr>
              <td>${balance.asset}</td>
              <td>${formatNumber(free)}</td>
              <td>${formatNumber(locked)}</td>
              <td>${formatNumber(total)}</td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
  
  $("balancesTable").innerHTML = table;
}

function updateTradesTable(trades) {
  if (!trades || trades.length === 0) {
    $("tradesTable").innerHTML = "<p>No trades found</p>";
    return;
  }
  
  const table = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Symbol</th>
          <th>Side</th>
          <th>Quantity</th>
          <th>Price</th>
          <th>Order ID</th>
        </tr>
      </thead>
      <tbody>
        ${trades.map(trade => `
          <tr>
            <td>${formatTimestamp(trade.timestamp)}</td>
            <td>${trade.symbol}</td>
            <td class="${trade.side === 'BUY' ? 'buy' : 'sell'}">${trade.side}</td>
            <td>${formatNumber(trade.quantity)}</td>
            <td>${formatCurrency(trade.price)}</td>
            <td>${trade.order_id || '-'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  $("tradesTable").innerHTML = table;
}

async function updatePortfolio() {
  try {
    const data = await fetchJSON("/api/portfolio");
    updateSummaryCards(data);
    updatePositionsTable(data.positions);
  } catch (e) {
    console.error("Portfolio update failed:", e);
  }
}

async function updateBalances() {
  try {
    const data = await fetchJSON("/api/balances");
    updateBalancesTable(data.balances);
  } catch (e) {
    console.error("Balances update failed:", e);
  }
}

async function updateTrades() {
  try {
    const data = await fetchJSON("/api/trades");
    updateTradesTable(data.trades);
  } catch (e) {
    console.error("Trades update failed:", e);
  }
}

function init() {
  updatePortfolio();
  updateBalances();
  updateTrades();
  
  // Refresh data every 5 seconds
  setInterval(updatePortfolio, 5000);
  setInterval(updateBalances, 10000);
  setInterval(updateTrades, 10000);
}

document.addEventListener("DOMContentLoaded", init);

// Dashboard functionality
let performanceChart;

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

// API functions
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Dashboard data loading
async function loadDashboardData() {
    try {
        // Load portfolio summary
        const portfolioResponse = await fetchJSON('/api/portfolio');
        updatePortfolioSummary(portfolioResponse);
        
        // Load bot configurations
        const botConfigsResponse = await fetchJSON('/api/bot-configs');
        updateBotConfigurations(botConfigsResponse.configs);
        
        // Load recent trades
        const tradesResponse = await fetchJSON('/api/trades?limit=10');
        updateRecentTrades(tradesResponse.trades);
        
        // Update statistics
        updateTradingStats(portfolioResponse.stats);
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showError('Failed to load dashboard data. Please try again.');
    }
}

function updatePortfolioSummary(data) {
    const summary = data.summary;
    const stats = data.stats;
    
    // Update overview cards
    const totalValue = summary.positions?.reduce((sum, pos) => sum + pos.total_value, 0) || 0;
    document.getElementById('totalValue').textContent = formatCurrency(totalValue);
    
    // Calculate total PnL (simplified)
    const totalPnl = summary.positions?.reduce((sum, pos) => {
        // This is a simplified PnL calculation
        return sum + (pos.total_value || 0);
    }, 0) || 0;
    
    document.getElementById('totalPnl').textContent = formatCurrency(totalPnl);
    document.getElementById('totalPnl').className = `value ${totalPnl >= 0 ? 'positive' : 'negative'}`;
    
    // Update other cards
    const activeBots = summary.positions?.length || 0;
    document.getElementById('activeBots').textContent = activeBots;
    
    const totalTrades = stats.total_trades || 0;
    document.getElementById('totalTrades').textContent = totalTrades;
}

function updateBotConfigurations(configs) {
    const container = document.getElementById('botConfigsList');
    container.innerHTML = '';
    
    if (!configs || configs.length === 0) {
        container.innerHTML = '<p class="no-data">No bot configurations found. Create your first bot!</p>';
        return;
    }
    
    configs.forEach(config => {
        const botCard = createBotCard(config);
        container.appendChild(botCard);
    });
}

function createBotCard(config) {
    const card = document.createElement('div');
    card.className = 'bot-card';
    card.innerHTML = `
        <div class="bot-header">
            <h3>${config.symbol}</h3>
            <span class="bot-status ${config.is_active ? 'active' : 'inactive'}">
                ${config.is_active ? 'Active' : 'Inactive'}
            </span>
        </div>
        <div class="bot-details">
            <div class="bot-param">
                <label>Buy Threshold:</label>
                <span>$${config.buy_threshold}</span>
            </div>
            <div class="bot-param">
                <label>Sell Threshold:</label>
                <span>$${config.sell_threshold}</span>
            </div>
            <div class="bot-param">
                <label>Quantity:</label>
                <span>${config.quantity}</span>
            </div>
            <div class="bot-param">
                <label>Mode:</label>
                <span>${config.dry_run ? 'Test' : 'Live'}</span>
            </div>
        </div>
        <div class="bot-actions">
            <button class="btn-small ${config.is_active ? 'btn-stop' : 'btn-start'}" 
                    onclick="toggleBot('${config.symbol}', ${!config.is_active})">
                ${config.is_active ? 'Stop' : 'Start'}
            </button>
            <button class="btn-small btn-edit" onclick="editBot('${config.symbol}')">
                Edit
            </button>
            <button class="btn-small btn-delete" onclick="deleteBot('${config.symbol}')">
                Delete
            </button>
        </div>
    `;
    return card;
}

function updateRecentTrades(trades) {
    const container = document.getElementById('recentTrades');
    container.innerHTML = '';
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<p class="no-data">No recent trades found.</p>';
        return;
    }
    
    trades.forEach(trade => {
        const tradeItem = createTradeItem(trade);
        container.appendChild(tradeItem);
    });
}

function createTradeItem(trade) {
    const item = document.createElement('div');
    item.className = 'trade-item';
    item.innerHTML = `
        <div class="trade-info">
            <div class="trade-symbol">${trade.symbol}</div>
            <div class="trade-side ${trade.side.toLowerCase()}">${trade.side}</div>
            <div class="trade-quantity">${trade.quantity}</div>
            <div class="trade-price">$${trade.price}</div>
            <div class="trade-type">${trade.trade_type}</div>
            <div class="trade-time">${formatTimestamp(trade.timestamp)}</div>
        </div>
    `;
    return item;
}

function updateTradingStats(stats) {
    if (!stats) return;
    
    document.getElementById('buyTrades').textContent = stats.buy_trades || 0;
    document.getElementById('sellTrades').textContent = stats.sell_trades || 0;
    document.getElementById('manualTrades').textContent = stats.manual_trades || 0;
    document.getElementById('botTrades').textContent = stats.bot_trades || 0;
    document.getElementById('totalVolume').textContent = formatCurrency(stats.total_volume || 0);
    
    const successRate = stats.total_trades > 0 ? 
        Math.round((stats.buy_trades / stats.total_trades) * 100) : 0;
    document.getElementById('successRate').textContent = `${successRate}%`;
}

// Bot management functions
async function toggleBot(symbol, activate) {
    try {
        if (activate) {
            // Start bot
            await fetchJSON('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    buy_threshold: 3000, // Default values
                    sell_threshold: 3200,
                    quantity: 0.01,
                    dry_run: true
                })
            });
        } else {
            // Stop bot
            await fetchJSON('/api/stop', { method: 'POST' });
        }
        
        // Refresh bot configurations
        const response = await fetchJSON('/api/bot-configs');
        updateBotConfigurations(response.configs);
        
        showSuccess(`Bot ${activate ? 'started' : 'stopped'} successfully`);
    } catch (error) {
        console.error('Failed to toggle bot:', error);
        showError('Failed to toggle bot. Please try again.');
    }
}

async function deleteBot(symbol) {
    if (!confirm(`Are you sure you want to delete the bot configuration for ${symbol}?`)) {
        return;
    }
    
    try {
        await fetchJSON(`/api/bot-config/${symbol}`, { method: 'DELETE' });
        
        // Refresh bot configurations
        const response = await fetchJSON('/api/bot-configs');
        updateBotConfigurations(response.configs);
        
        showSuccess('Bot configuration deleted successfully');
    } catch (error) {
        console.error('Failed to delete bot:', error);
        showError('Failed to delete bot configuration. Please try again.');
    }
}

function editBot(symbol) {
    // For now, just show an alert. This could be expanded to show an edit modal
    alert(`Edit functionality for ${symbol} bot will be implemented soon.`);
}

// Modal functions
function openModal() {
    document.getElementById('createBotModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('createBotModal').style.display = 'none';
    document.getElementById('createBotForm').reset();
}

async function createBot(event) {
    event.preventDefault();
    
    const formData = {
        symbol: document.getElementById('botSymbol').value,
        buy_threshold: parseFloat(document.getElementById('botBuyThreshold').value),
        sell_threshold: parseFloat(document.getElementById('botSellThreshold').value),
        quantity: parseFloat(document.getElementById('botQuantity').value),
        dry_run: document.getElementById('botDryRun').checked,
        is_active: false,
        bot_type: 'THRESHOLD'
    };
    
    try {
        await fetchJSON('/api/bot-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        closeModal();
        
        // Refresh bot configurations
        const response = await fetchJSON('/api/bot-configs');
        updateBotConfigurations(response.configs);
        
        showSuccess('Bot configuration created successfully');
    } catch (error) {
        console.error('Failed to create bot:', error);
        showError('Failed to create bot configuration. Please try again.');
    }
}

// Notification functions
function showSuccess(message) {
    // Simple success notification
    alert(`Success: ${message}`);
}

function showError(message) {
    // Simple error notification
    alert(`Error: ${message}`);
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadDashboardData();
    
    // Set up event listeners
    document.getElementById('createBot').addEventListener('click', openModal);
    document.getElementById('refreshBots').addEventListener('click', loadDashboardData);
    document.getElementById('createBotForm').addEventListener('submit', createBot);
    
    // Modal close events
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('createBotModal');
        if (event.target === modal) {
            closeModal();
        }
    });
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

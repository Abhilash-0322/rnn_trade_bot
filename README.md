# RNN Crypto Bot (Binance Testnet)

Flask-based modular crypto trading bot using Binance Spot Testnet. Features threshold strategy, portfolio tracking, multi-currency support, and local price storage.

## ✨ Features

### 🎯 Trading Bot
- **Threshold Strategy**: Buy at low threshold, sell at high threshold
- **Position Tracking**: Prevents repeated orders, tracks holdings
- **Dynamic Dry-Run**: Toggle between simulation and real trading
- **Real-time Monitoring**: Live price updates and bot status

### 📊 Portfolio Management
- **Position Tracking**: Real-time PnL calculation
- **Trade History**: Complete record of all executed trades
- **Balance Monitoring**: Account balances from Binance
- **Portfolio Dashboard**: Visual summary with profit/loss tracking

### 📈 Multi-Currency Support
- **Symbol Selection**: Choose from 50+ trading pairs
- **Time-based Charts**: 1H, 1D, 3D, 1W, 1M periods
- **Historical Data**: Local CSV storage for price history
- **Interactive Charts**: Chart.js with zoom and tooltips

### 💾 Local Storage
- **CSV Database**: Automatic price history storage
- **Data Persistence**: Maintains historical data across restarts
- **Period Filtering**: Efficient time-based data retrieval
- **Auto Cleanup**: Removes old data to save space

## 🚀 Setup

1. **Clone and setup environment**:
```bash
cd /home/abhilash/codespace/rnn_crypto
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Binance Testnet**:
```bash
cp .env.example .env
# Edit .env and add your Binance testnet API keys
# Get keys from: https://testnet.binance.vision/
```

3. **Run the application**:
```bash
python run.py
```

4. **Access the application**:
- **Trading Bot**: `http://localhost:5000/`
- **Portfolio**: `http://localhost:5000/portfolio`


## Overview
![RNN Crypto Trading Bot Overview](rnn_oveview.svg)

### Current Architecture (Colorful)
```dot
digraph RnnCryptoCurrent {
  rankdir=LR;
  node [shape=box, style=filled];
  edge [color=gray];

  subgraph cluster_flask {
    label="Flask Application";
    style=filled;
    fillcolor=lightblue;
    
    "create_app()" [label="app/__init__.py\ncreate_app()", fillcolor=lightcyan];
    "AuthManager" [label="auth/auth_manager.py\nAuthManager + Flask-Login", fillcolor=lightgreen];
    "MongoDB" [label="database/mongodb.py\nMongoDB client + collections\nusers, trades, bot_configs, prices", fillcolor=lightyellow];
    "BinanceClient" [label="binance_client.py\nSpot API wrapper\ndry_run support", fillcolor=lightcoral];
    "TradingBotManager" [label="services/trading_bot.py\nThreaded bot manager", fillcolor=lightpink];
    "PortfolioManager" [label="services/portfolio.py\nIn-memory positions/trades", fillcolor=lightsteelblue];
    "PriceStorage" [label="services/price_storage.py\nCSV + Mongo dual-write", fillcolor=lightseagreen];

    "Blueprint: api" [label="app/api_routes.py\n/api/* endpoints", shape=component, fillcolor=orange];
    "Blueprint: auth" [label="app/routes/auth.py\n/login, /register, /logout", shape=component, fillcolor=orange];

    "create_app()" -> "AuthManager";
    "create_app()" -> "MongoDB";
    "create_app()" -> "BinanceClient";
    "create_app()" -> "TradingBotManager";
    "create_app()" -> "PortfolioManager";
    "create_app()" -> "PriceStorage";
    "create_app()" -> "Blueprint: api";
    "create_app()" -> "Blueprint: auth";

    "TradingBotManager" -> "TradingBot thread" [label="start(symbol, buy, sell, qty)"];
    "TradingBot thread" [label="services/trading_bot.py\nloops: get_price → BUY/SELL", fillcolor=lightgoldenrodyellow];
  }

  subgraph cluster_storage {
    label="Storage";
    style=filled;
    fillcolor=lightyellow;
    
    "CSV files" [label="data/*.csv\n<symbol>_prices.csv", shape=cylinder, fillcolor=lightcoral];
    "Mongo collections" [label="MongoDB\nusers, trades, bot_configs, prices", shape=cylinder, fillcolor=lightgreen];
  }

  subgraph cluster_frontend {
    label="Frontend (static)";
    style=filled;
    fillcolor=lightgreen;
    
    "index.html + app.js" [label="Landing + streaming chart\nfetch /api/price, /status, /price-history", fillcolor=lightcyan];
    "dashboard.html + dashboard.js" [label="Dashboard\n/auth, /api/portfolio, /api/bot-configs, /api/trades", fillcolor=lightpink];
    "portfolio.html + portfolio.js" [label="Portfolio\n/api/portfolio, /api/balances, /api/trades", fillcolor=lightsteelblue];
    "auth pages" [label="auth/login.html, auth/register.html", fillcolor=lightseagreen];
  }

  // Data flows
  "index.html + app.js" -> "Blueprint: api" [label="GET /api/price, /status, /price-history"];
  "dashboard.html + dashboard.js" -> "Blueprint: api" [label="GET /api/portfolio, /api/bot-configs, /api/trades\nPOST /api/start, /api/stop"];
  "portfolio.html + portfolio.js" -> "Blueprint: api" [label="GET /api/portfolio, /api/balances, /api/trades"];
  "auth pages" -> "Blueprint: auth" [label="POST /login, /register"];

  "Blueprint: api" -> "TradingBotManager" [label="start/stop/status"];
  "Blueprint: api" -> "PortfolioManager" [label="update positions on trades"];
  "Blueprint: api" -> "MongoDB" [label="save trades, configs, analytics queries"];
  "Blueprint: api" -> "BinanceClient" [label="market data, orders"];
  "Blueprint: api" -> "PriceStorage" [label="save_price(symbol, price)"];

  "PriceStorage" -> "CSV files" [label="append ticks"];
  "PriceStorage" -> "Mongo collections" [label="prices: save_price_point()"];
  "TradingBot thread" -> "BinanceClient" [label="get_price / place_market_order"];
  "TradingBot thread" -> "MongoDB" [label="save trades (BOT_THRESHOLD)"];
  "TradingBot thread" -> "PortfolioManager" [label="add_trade BUY/SELL"];

  // Auth
  "AuthManager" -> "MongoDB" [label="load/create users"];
  "auth pages" -> "AuthManager" [label="Flask-Login session"];
}
```

### Enhanced RNN Architecture
```dot
digraph RnnCryptoEnhanced {
  rankdir=TB;
  node [shape=box, style=filled, fillcolor=lightblue];
  edge [color=gray];

  subgraph cluster_data_sources {
    label="Data Sources & Inputs";
    style=filled;
    fillcolor=lightyellow;
    
    "Binance API" [shape=cylinder, fillcolor=orange];
    "Historical CSV" [shape=cylinder, fillcolor=orange];
    "MongoDB Prices" [shape=cylinder, fillcolor=orange];
    "Technical Indicators" [shape=note, fillcolor=lightgreen];
    "Market Sentiment" [shape=note, fillcolor=lightgreen];
    "Volume Data" [shape=note, fillcolor=lightgreen];
  }

  subgraph cluster_data_processing {
    label="Data Processing & Feature Engineering";
    style=filled;
    fillcolor=lightcyan;
    
    "Data Preprocessor" [label="Data Preprocessor\n- Normalize prices\n- Calculate returns\n- Handle missing data\n- Feature scaling"];
    "Feature Extractor" [label="Feature Extractor\n- Technical indicators\n- Price patterns\n- Volume analysis\n- Market microstructure"];
    "Sequence Builder" [label="Sequence Builder\n- Create time windows\n- Sliding windows\n- Sequence padding\n- Label generation"];
  }

  subgraph cluster_rnn_models {
    label="RNN Models & Architecture";
    style=filled;
    fillcolor=lightpink;
    
    "LSTM Model" [label="LSTM Model\n- Long-term dependencies\n- Price trend prediction\n- Sequence length: 60-120\n- Hidden layers: 128-256"];
    "GRU Model" [label="GRU Model\n- Faster training\n- Momentum prediction\n- Sequence length: 30-60\n- Hidden layers: 64-128"];
    "Attention Mechanism" [label="Attention Layer\n- Focus on important\n  time steps\n- Weighted predictions\n- Interpretable results"];
    "Ensemble Predictor" [label="Ensemble Predictor\n- Combine LSTM/GRU\n- Voting mechanism\n- Confidence scoring\n- Risk assessment"];
  }

  subgraph cluster_training {
    label="Model Training & Validation";
    style=filled;
    fillcolor=lightcoral;
    
    "Training Pipeline" [label="Training Pipeline\n- Split train/val/test\n- Cross-validation\n- Hyperparameter tuning\n- Early stopping"];
    "Backtesting Engine" [label="Backtesting Engine\n- Historical simulation\n- Walk-forward analysis\n- Performance metrics\n- Risk evaluation"];
    "Model Registry" [label="Model Registry\n- Version control\n- A/B testing\n- Model comparison\n- Deployment tracking"];
  }

  subgraph cluster_prediction {
    label="Real-time Prediction & Signals";
    style=filled;
    fillcolor=lightsteelblue;
    
    "Signal Generator" [label="Signal Generator\n- Buy/Sell/Hold signals\n- Confidence scores\n- Risk levels\n- Position sizing"];
    "Market Regime Detector" [label="Market Regime Detector\n- Bull/Bear/Sideways\n- Volatility regimes\n- Trend strength\n- Market conditions"];
    "Portfolio Optimizer" [label="Portfolio Optimizer\n- Asset allocation\n- Risk management\n- Rebalancing logic\n- Capital efficiency"];
  }

  subgraph cluster_flask_app {
    label="Enhanced Flask Application";
    style=filled;
    fillcolor=lightblue;
    
    "RNNService" [label="services/rnn_service.py\n- Model loading\n- Real-time inference\n- Signal generation\n- Performance monitoring"];
    "Enhanced TradingBot" [label="services/trading_bot.py\n- RNN-based decisions\n- Dynamic thresholds\n- Risk management\n- Position sizing"];
    "SignalProcessor" [label="services/signal_processor.py\n- Signal validation\n- Market impact\n- Execution timing\n- Slippage control"];
    
    "Blueprint: api" [label="app/api_routes.py\nEnhanced endpoints:\n/api/predict\n/api/signals\n/api/model-status\n/api/backtest", shape=component];
    "Blueprint: auth" [label="app/routes/auth.py", shape=component];
  }

  subgraph cluster_storage {
    label="Enhanced Storage";
    style=filled;
    fillcolor=lightyellow;
    
    "Model Storage" [label="models/\n- Saved model files\n- Checkpoints\n- Configurations\n- Performance logs"];
    "Prediction Cache" [label="MongoDB\npredictions collection\n- Real-time predictions\n- Signal history\n- Model performance\n- Backtest results"];
    "Feature Store" [label="MongoDB\nfeatures collection\n- Calculated features\n- Technical indicators\n- Market data\n- Sentiment scores"];
  }

  subgraph cluster_frontend {
    label="Enhanced Frontend";
    style=filled;
    fillcolor=lightgreen;
    
    "Prediction Dashboard" [label="prediction.html + prediction.js\n- RNN predictions\n- Signal visualization\n- Model confidence\n- Performance metrics"];
    "Backtest Interface" [label="backtest.html + backtest.js\n- Historical simulation\n- Strategy comparison\n- Risk analysis\n- Performance charts"];
    "Model Monitor" [label="model_monitor.html + model_monitor.js\n- Model health\n- Prediction accuracy\n- Drift detection\n- Retraining alerts"];
  }

  // Data Flow Connections
  "Binance API" -> "Data Preprocessor" [label="Real-time prices\nOHLCV data"];
  "Historical CSV" -> "Data Preprocessor" [label="Historical prices\nVolume data"];
  "MongoDB Prices" -> "Data Preprocessor" [label="Stored price data"];
  "Technical Indicators" -> "Feature Extractor" [label="RSI, MACD, Bollinger\nMoving averages"];
  "Market Sentiment" -> "Feature Extractor" [label="News sentiment\nSocial media\nFear & Greed index"];
  "Volume Data" -> "Feature Extractor" [label="Volume patterns\nOrder book data"];

  "Data Preprocessor" -> "Feature Extractor" [label="Cleaned data"];
  "Feature Extractor" -> "Sequence Builder" [label="Engineered features"];
  "Sequence Builder" -> "LSTM Model" [label="Training sequences"];
  "Sequence Builder" -> "GRU Model" [label="Training sequences"];

  "LSTM Model" -> "Attention Mechanism" [label="Hidden states"];
  "GRU Model" -> "Attention Mechanism" [label="Hidden states"];
  "Attention Mechanism" -> "Ensemble Predictor" [label="Weighted predictions"];

  "Training Pipeline" -> "LSTM Model" [label="Train/validate"];
  "Training Pipeline" -> "GRU Model" [label="Train/validate"];
  "Backtesting Engine" -> "Model Registry" [label="Performance results"];
  "Model Registry" -> "RNNService" [label="Load best model"];

  "Ensemble Predictor" -> "Signal Generator" [label="Price predictions\nConfidence scores"];
  "Signal Generator" -> "Market Regime Detector" [label="Market analysis"];
  "Market Regime Detector" -> "Portfolio Optimizer" [label="Regime info"];
  "Portfolio Optimizer" -> "Enhanced TradingBot" [label="Trading decisions"];

  "RNNService" -> "SignalProcessor" [label="Real-time signals"];
  "SignalProcessor" -> "Enhanced TradingBot" [label="Validated signals"];
  "Enhanced TradingBot" -> "Blueprint: api" [label="Trading actions"];

  // Storage connections
  "Model Storage" -> "RNNService" [label="Load models"];
  "Prediction Cache" -> "RNNService" [label="Cache predictions"];
  "Feature Store" -> "Feature Extractor" [label="Stored features"];

  // Frontend connections
  "Blueprint: api" -> "Prediction Dashboard" [label="GET /api/predict\nGET /api/signals"];
  "Blueprint: api" -> "Backtest Interface" [label="POST /api/backtest\nGET /api/backtest-results"];
  "Blueprint: api" -> "Model Monitor" [label="GET /api/model-status\nGET /api/performance"];

  // Real-time data flow
  "Binance API" -> "RNNService" [label="Live price feed"];
  "RNNService" -> "Prediction Cache" [label="Save predictions"];
  "RNNService" -> "Feature Store" [label="Save features"];

  // Feedback loop
  "Enhanced TradingBot" -> "Backtesting Engine" [label="Trade results"];
  "Backtesting Engine" -> "Training Pipeline" [label="Performance feedback"];
  "Training Pipeline" -> "Model Registry" [label="Updated models"];

  // Monitoring
  "Model Monitor" -> "Model Registry" [label="Monitor performance"];
  "Model Monitor" -> "Training Pipeline" [label="Trigger retraining"];
}
```

## 📋 API Endpoints

### Trading
- `GET /api/price?symbol=ETHUSDT` - Current price
- `GET /api/price-history?symbol=ETHUSDT&period=1d` - Historical prices
- `GET /api/symbols` - Available trading pairs
- `GET /api/status` - Bot status and dry-run setting
- `POST /api/start` - Start trading bot
- `POST /api/stop` - Stop trading bot
- `POST /api/order` - Place manual order

### Portfolio
- `GET /api/portfolio` - Portfolio summary and positions
- `GET /api/trades` - Recent trade history
- `GET /api/balances` - Account balances

## 🎮 Usage

### Trading Bot Page
1. **Select Currency**: Choose from dropdown (ETH, BTC, BNB, etc.)
2. **Set Chart Period**: 1H, 1D, 3D, 1W, 1M
3. **Configure Thresholds**: Set buy/sell prices
4. **Toggle Dry-Run**: Test without real orders
5. **Start Bot**: Begin automated trading

### Portfolio Page
- **Summary Cards**: Total PnL, realized/unrealized gains
- **Positions Table**: Current holdings with entry prices
- **Balances Table**: All account assets
- **Trades Table**: Complete trade history

## 📁 Data Storage

Price data is automatically stored in CSV files:
```
data/
├── ethusdt_prices.csv
├── btcusdt_prices.csv
└── ...
```

Each CSV contains: `timestamp, price, datetime`

## 🔧 Configuration

Environment variables in `.env`:
```bash
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
BINANCE_BASE_URL=https://testnet.binance.vision
DEFAULT_SYMBOL=ETHUSDT
ORDER_QUANTITY=0.01
DRY_RUN=true
```

## 🧪 Testing

Test Binance API connectivity:
```bash
python test_binance_api.py
```

## 🔮 Roadmap
- [ ] RNN-based signal generation
- [ ] WebSocket price streaming
- [ ] Advanced chart indicators
- [ ] Backtesting framework
- [ ] Risk management features
- [ ] Multi-exchange support

## 📝 Notes
- Uses Binance Spot Testnet for safe testing
- `DRY_RUN=true` simulates orders without execution
- Local CSV storage provides historical data persistence
- Chart periods: 1H, 1D, 3D, 1W, 1M
- Supports 50+ trading pairs from Binance

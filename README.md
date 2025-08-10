# Live AI Crypto Trading Bot - Azure Deployment

## 🚀 Live Trading Features

This bot has been upgraded to **LIVE TRADING** with aggressive settings and real money execution on Binance.US.

### Key Features
- **Live-Only Mode**: No paper trading - real money, real profits
- **Aggressive Strategy**: 10% per-trade risk on 80% of portfolio
- **Risk Management**: 30% daily loss stop with auto-halt
- **Symbols**: BTCUSD and SOLUSD (USD-quoted pairs)
- **Enhanced Features**: MACD analysis, whale detection, dynamic sizing
- **Emergency Controls**: Hard kill switch and live trading toggle

## 📊 Trading Configuration

### Risk Parameters
- **Per-Trade Risk**: 10% of managed equity
- **Daily Loss Stop**: 30% (auto-halt all trading)
- **Managed Fraction**: 80% of total portfolio
- **Max Concurrent Positions**: 20
- **Max Consecutive Losses**: 4 (then 2-hour cooldown)

### Technical Analysis
- **MACD**: 12/26/9 settings
- **EMA**: 200-period trend filter
- **ATR**: 14-period for stop/target calculation
- **Volume**: Z-score analysis for confirmation
- **Whale Detection**: Large trade and imbalance monitoring

## 🛠️ Setup Instructions

### 1. Environment Variables
Create a `.env` file with your Binance.US credentials:

```bash
BINANCE_US_API_KEY=your_api_key_here
BINANCE_US_API_SECRET=your_api_secret_here
TRADE_ENABLED=false
HARD_KILL=false
PORT=8080
LOG_LEVEL=INFO
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Locally
```bash
python app.py
```

### 4. Enable Live Trading
1. Set `TRADE_ENABLED=true` in your environment
2. Use the dashboard toggle to enable/disable trading
3. Use HARD KILL for emergency stops

## 🔧 Core Components

### Trading Engine (`core/engine.py`)
- Main trading logic and signal processing
- Risk gate validation before each trade
- Position sizing and order management

### Signal Generation (`core/signals.py`)
- MACD trend analysis
- EMA 200 trend filter
- Volume spike detection
- Whale activity monitoring

### Risk Management (`core/risk.py`)
- Daily loss tracking and limits
- Consecutive loss streak protection
- Cooldown periods after losses
- Position allocation controls

### Live Broker (`core/broker.py`)
- Market order execution
- OCO (One-Cancels-Other) emulation
- Stop-loss and take-profit management
- Order reconciliation

### Data Feed (`core/datafeed.py`)
- Real-time market data from Binance.US
- Whale transaction detection
- Portfolio equity calculation

## 📈 Dashboard Features

### Live Controls
- **Trade Toggle**: Enable/disable live trading
- **Hard Kill**: Emergency stop for all new trades
- **Real-time Status**: System health and connectivity

### Performance Monitoring
- **Daily P&L**: Real-time profit/loss tracking
- **Portfolio Value**: Live equity updates
- **Risk Progress**: Daily stop limit visualization
- **Trade History**: Recent execution details

### Risk Indicators
- **Loss Streak**: Consecutive losing trades
- **Cooldown Timer**: Time remaining in cooldown
- **Error Count**: System error tracking
- **Position Limits**: Current vs maximum positions

## ⚠️ Important Notes

### Live Trading Warnings
- This bot trades with **REAL MONEY**
- Losses can be substantial (up to 30% daily)
- Always monitor the dashboard regularly
- Use the HARD KILL switch if needed

### API Requirements
- Binance.US account with trading enabled
- API keys with spot trading permissions
- Sufficient balance for position sizing

### Risk Disclaimer
- Cryptocurrency trading involves substantial risk
- Past performance does not guarantee future results
- Only trade with money you can afford to lose
- The bot operates autonomously once enabled

## 🚀 Deployment

### Azure Container Instances
The bot is configured for Azure deployment with:
- Automatic restarts on failure
- Environment variable configuration
- 24/7 operation without sleep issues
- Persistent logging and monitoring

### GitHub Actions
Automated deployment pipeline:
1. Push changes to main branch
2. GitHub Actions builds and deploys
3. Azure updates the running container
4. Zero-downtime deployment

## 📞 Support

For issues or questions:
1. Check the dashboard error count
2. Review application logs
3. Verify API connectivity
4. Use HARD KILL if needed

**Remember**: This is live trading software. Always monitor your positions and be prepared to intervene manually if needed.




#!/usr/bin/env python3
"""
Enhanced AI Crypto Trading Bot - Live Trading Edition
Advanced trading algorithms with real-time execution on Binance.US
"""

import os
import logging
import threading
import time
import json
import yaml
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from dotenv import load_dotenv
from binance.client import Client

# Import core trading modules
from core.engine import Engine
from core.broker import LiveBroker
from core.datafeed import DataFeed
from core.account import Account
from core.storage import Storage
from core.risk import RiskEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
with open('settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Global state
bot_state = {
    "status": "initializing",
    "trade_enabled": os.getenv('TRADE_ENABLED', 'false').lower() == 'true',
    "hard_kill": os.getenv('HARD_KILL', 'false').lower() == 'true',
    "last_scan_time": None,
    "signals_detected": 0,
    "trades_last_24h": 0,
    "portfolio_value": 0.0,
    "managed_equity": 0.0,
    "uptime": datetime.now().isoformat(),
    "total_trades": 0,
    "winning_trades": 0,
    "total_profit": 0.0,
    "error_count": 0,
    "daily_pnl": 0.0,
    "daily_pnl_percent": 0.0,
    "loss_streak": 0,
    "cooldown_until": 0,
    "open_positions": [],
    "recent_trades": []
}

# Trading components
binance_client = None
trading_engine = None
storage = None

def initialize_trading_components():
    """Initialize all trading components"""
    global binance_client, trading_engine, storage
    
    try:
        # Initialize Binance client
        api_key = os.getenv('BINANCE_US_API_KEY')
        api_secret = os.getenv('BINANCE_US_API_SECRET')
        
        if not api_key or not api_secret:
            logger.warning("Binance API credentials not found - running in demo mode")
            bot_state["status"] = "demo_mode"
            return False
        
        binance_client = Client(api_key, api_secret, tld='us')
        
        # Test connection
        account_info = binance_client.get_account()
        logger.info("Successfully connected to Binance.US")
        
        # Initialize components
        datafeed = DataFeed(binance_client, logger)
        account = Account(binance_client, logger)
        broker = LiveBroker(binance_client, account.precision_map())
        storage = Storage("data", logger)
        
        # Initialize trading engine
        trading_engine = Engine(broker, datafeed, account, config, storage, logger)
        
        # Update portfolio value
        bot_state["portfolio_value"] = datafeed.get_equity_usd()
        bot_state["managed_equity"] = bot_state["portfolio_value"] * config['account']['managed_fraction']
        
        bot_state["status"] = "online"
        logger.info("All trading components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize trading components: {e}")
        bot_state["status"] = "error"
        bot_state["error_count"] += 1
        return False

@app.route("/")
def dashboard():
    """Enhanced live trading dashboard"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live AI Crypto Trading Bot - Azure Deployment</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1600px; margin: 0 auto; }
            .header { 
                background: rgba(255,255,255,0.95); 
                padding: 30px; 
                border-radius: 15px; 
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                position: relative;
            }
            .header h1 { color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }
            .header p { color: #7f8c8d; font-size: 1.2em; }
            
            .live-controls {
                position: absolute;
                top: 20px;
                right: 20px;
                display: flex;
                gap: 15px;
                align-items: center;
            }
            
            .toggle-switch {
                position: relative;
                width: 60px;
                height: 30px;
                background: #ccc;
                border-radius: 15px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .toggle-switch.active { background: #27ae60; }
            
            .toggle-slider {
                position: absolute;
                top: 3px;
                left: 3px;
                width: 24px;
                height: 24px;
                background: white;
                border-radius: 50%;
                transition: transform 0.3s;
            }
            
            .toggle-switch.active .toggle-slider { transform: translateX(30px); }
            
            .kill-switch {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                transition: background 0.3s;
            }
            
            .kill-switch:hover { background: #c0392b; }
            
            .status-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
                gap: 25px; 
                margin-bottom: 30px;
            }
            .status-card { 
                background: rgba(255,255,255,0.95); 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                transition: transform 0.3s ease;
            }
            .status-card:hover { transform: translateY(-5px); }
            .status-online { border-left: 6px solid #27ae60; }
            .status-trading { border-left: 6px solid #3498db; }
            .status-performance { border-left: 6px solid #e74c3c; }
            .status-risk { border-left: 6px solid #f39c12; }
            .status-value { 
                font-size: 2.2em; 
                font-weight: bold; 
                color: #2c3e50; 
                margin: 10px 0;
            }
            
            .progress-bar {
                width: 100%;
                height: 20px;
                background: #ecf0f1;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);
                transition: width 0.3s ease;
            }
            
            .loss-streak {
                display: inline-block;
                background: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }
            
            .cooldown-timer {
                background: #f39c12;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-left: 10px;
            }
            
            .trades-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            
            .trades-table th,
            .trades-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ecf0f1;
            }
            
            .trades-table th {
                background: #f8f9fa;
                font-weight: bold;
            }
            
            .profit { color: #27ae60; font-weight: bold; }
            .loss { color: #e74c3c; font-weight: bold; }
            
            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                margin-top: 15px;
                transition: background 0.3s ease;
            }
            .refresh-btn:hover { background: #2980b9; }
            
            @media (max-width: 768px) {
                .header h1 { font-size: 2em; }
                .status-grid { grid-template-columns: 1fr; }
                .status-value { font-size: 1.8em; }
                .live-controls { position: static; margin-top: 20px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="live-controls">
                    <label>LIVE TRADING</label>
                    <div class="toggle-switch {{ 'active' if trade_enabled else '' }}" onclick="toggleTrading()">
                        <div class="toggle-slider"></div>
                    </div>
                    <button class="kill-switch" onclick="hardKill()">HARD KILL</button>
                </div>
                <h1>🚀 Live AI Crypto Trading Bot</h1>
                <p>Aggressive Live Trading • Azure Cloud • Real Money • Real Profits</p>
            </div>
            
            <div class="status-grid">
                <div class="status-card status-online">
                    <h3><span style="color: {{ status_color }};">●</span> System Status</h3>
                    <div class="status-value">{{ status.upper() }}</div>
                    <p><strong>Live Trading:</strong> {{ 'ENABLED' if trade_enabled else 'DISABLED' }}</p>
                    <p><strong>Hard Kill:</strong> {{ 'ACTIVE' if hard_kill else 'INACTIVE' }}</p>
                    <p><strong>Uptime:</strong> {{ uptime_display }}</p>
                    <p><strong>Last Scan:</strong> {{ last_scan or 'Starting...' }}</p>
                </div>
                
                <div class="status-card status-trading">
                    <h3>💰 Portfolio & Equity</h3>
                    <div class="status-value">${{ "%.2f"|format(portfolio_value) }}</div>
                    <p><strong>Managed Equity:</strong> ${{ "%.2f"|format(managed_equity) }}</p>
                    <p><strong>Trades (24h):</strong> {{ trades_24h }}</p>
                    <p><strong>Total Trades:</strong> {{ total_trades }}</p>
                    <p><strong>Open Positions:</strong> {{ open_positions|length }}</p>
                </div>
                
                <div class="status-card status-performance">
                    <h3>📈 Daily Performance</h3>
                    <div class="status-value {{ 'profit' if daily_pnl >= 0 else 'loss' }}">${{ "%.2f"|format(daily_pnl) }}</div>
                    <p><strong>Daily P&L %:</strong> <span class="{{ 'profit' if daily_pnl_percent >= 0 else 'loss' }}">{{ "%.2f"|format(daily_pnl_percent) }}%</span></p>
                    <p><strong>Total Profit:</strong> <span class="{{ 'profit' if total_profit >= 0 else 'loss' }}">${{ "%.2f"|format(total_profit) }}</span></p>
                    <p><strong>Win Rate:</strong> {{ win_rate }}%</p>
                    
                    <div style="margin-top: 15px;">
                        <label>Daily Stop Progress (30% limit)</label>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ daily_stop_progress }}%;"></div>
                        </div>
                        <small>{{ "%.1f"|format(daily_stop_progress) }}% of daily stop limit</small>
                    </div>
                </div>
                
                <div class="status-card status-risk">
                    <h3>🛡️ Risk Management</h3>
                    <p><strong>Error Count:</strong> {{ error_count }}</p>
                    <p><strong>Loss Streak:</strong> 
                        {% if loss_streak > 0 %}
                            <span class="loss-streak">{{ loss_streak }} losses</span>
                            {% if cooldown_remaining > 0 %}
                                <span class="cooldown-timer">{{ cooldown_remaining }}m cooldown</span>
                            {% endif %}
                        {% else %}
                            <span style="color: #27ae60;">None</span>
                        {% endif %}
                    </p>
                    <p><strong>Daily Risk Used:</strong> {{ "%.1f"|format(daily_stop_progress) }}%</p>
                    <p><strong>Max Positions:</strong> {{ config.limits.max_trades_day }}</p>
                </div>
            </div>
            
            {% if recent_trades %}
            <div class="status-card">
                <h3>📊 Recent Trades</h3>
                <table class="trades-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>P&L</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for trade in recent_trades[-10:] %}
                        <tr>
                            <td>{{ trade.timestamp[:16] }}</td>
                            <td>{{ trade.symbol }}</td>
                            <td>{{ trade.side }}</td>
                            <td>{{ trade.quantity }}</td>
                            <td>${{ "%.2f"|format(trade.price) }}</td>
                            <td class="{{ 'profit' if trade.pnl >= 0 else 'loss' }}">${{ "%.2f"|format(trade.pnl) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            <div style="text-align: center; color: rgba(255,255,255,0.9); margin-top: 30px;">
                <p>⚡ <strong>Live Trading Active</strong> • 🎯 Aggressive Strategy • 💎 Real Money Management</p>
                <p>🔥 BTCUSD & SOLUSD • 📊 MACD + Whale Detection • 🛡️ 30% Daily Stop</p>
                <button class="refresh-btn" onclick="location.reload()">Refresh Dashboard</button>
            </div>
        </div>
        
        <script>
            function toggleTrading() {
                fetch('/api/trading/toggle', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        }
                    });
            }
            
            function hardKill() {
                if (confirm('Are you sure you want to activate HARD KILL? This will stop all new trades immediately.')) {
                    fetch('/api/trading/hard-kill', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                location.reload();
                            }
                        });
                }
            }
            
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """, 
    status=bot_state["status"],
    status_color="#27ae60" if bot_state["status"] == "online" else "#e74c3c",
    trade_enabled=bot_state["trade_enabled"],
    hard_kill=bot_state["hard_kill"],
    uptime_display=datetime.now().strftime("%H:%M:%S UTC"),
    portfolio_value=bot_state["portfolio_value"],
    managed_equity=bot_state["managed_equity"],
    last_scan=bot_state["last_scan_time"],
    trades_24h=bot_state["trades_last_24h"],
    total_trades=bot_state["total_trades"],
    open_positions=bot_state["open_positions"],
    daily_pnl=bot_state["daily_pnl"],
    daily_pnl_percent=bot_state["daily_pnl_percent"],
    total_profit=bot_state["total_profit"],
    win_rate=int((bot_state["winning_trades"] / max(bot_state["total_trades"], 1)) * 100),
    error_count=bot_state["error_count"],
    loss_streak=bot_state["loss_streak"],
    cooldown_remaining=max(0, int((bot_state["cooldown_until"] - time.time()) / 60)),
    daily_stop_progress=min(100, abs(bot_state["daily_pnl_percent"]) / 30 * 100),
    recent_trades=bot_state["recent_trades"],
    config=config
    )

@app.route("/api/trading/toggle", methods=["POST"])
def toggle_trading():
    """Toggle live trading on/off"""
    bot_state["trade_enabled"] = not bot_state["trade_enabled"]
    
    # Update environment variable
    os.environ['TRADE_ENABLED'] = str(bot_state["trade_enabled"]).lower()
    
    logger.info(f"Live trading {'ENABLED' if bot_state['trade_enabled'] else 'DISABLED'}")
    
    return jsonify({
        "success": True,
        "trade_enabled": bot_state["trade_enabled"],
        "message": f"Live trading {'ENABLED' if bot_state['trade_enabled'] else 'DISABLED'}"
    })

@app.route("/api/trading/hard-kill", methods=["POST"])
def hard_kill():
    """Emergency stop - halt all new trades"""
    bot_state["hard_kill"] = True
    bot_state["trade_enabled"] = False
    
    # Update environment variables
    os.environ['HARD_KILL'] = 'true'
    os.environ['TRADE_ENABLED'] = 'false'
    
    logger.warning("HARD KILL ACTIVATED - All new trades halted")
    
    return jsonify({
        "success": True,
        "message": "HARD KILL activated - all new trades stopped"
    })

@app.route("/api/status")
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": bot_state["status"],
        "trade_enabled": bot_state["trade_enabled"],
        "hard_kill": bot_state["hard_kill"],
        "portfolio_value": bot_state["portfolio_value"],
        "managed_equity": bot_state["managed_equity"],
        "daily_pnl": bot_state["daily_pnl"],
        "error_count": bot_state["error_count"],
        "uptime": bot_state["uptime"]
    })

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if bot_state["status"] in ["online", "demo_mode"] else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "trading_active": bot_state["trade_enabled"] and not bot_state["hard_kill"]
    })

def trading_loop():
    """Main trading loop"""
    while True:
        try:
            if bot_state["hard_kill"]:
                logger.info("Hard kill active - skipping trading loop")
                time.sleep(60)
                continue
                
            if not bot_state["trade_enabled"]:
                time.sleep(30)
                continue
                
            if bot_state["status"] != "online" or not trading_engine:
                time.sleep(60)
                continue
            
            # Update scan time
            bot_state["last_scan_time"] = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
            
            # Run trading logic for each symbol
            for symbol in config['symbols']:
                try:
                    trading_engine.tick(symbol)
                except Exception as e:
                    logger.error(f"Error in trading tick for {symbol}: {e}")
                    bot_state["error_count"] += 1
            
            # Update portfolio value
            if binance_client:
                try:
                    datafeed = DataFeed(binance_client, logger)
                    bot_state["portfolio_value"] = datafeed.get_equity_usd()
                    bot_state["managed_equity"] = bot_state["portfolio_value"] * config['account']['managed_fraction']
                except Exception as e:
                    logger.error(f"Error updating portfolio value: {e}")
            
            # Update recent trades
            if storage:
                bot_state["recent_trades"] = storage.get_recent_trades(20)
            
            logger.info(f"Trading scan completed - Portfolio: ${bot_state['portfolio_value']:.2f}")
            
            # Sleep for scan interval
            time.sleep(60)  # 1 minute between scans
            
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            bot_state["error_count"] += 1
            time.sleep(60)

def start_background_tasks():
    """Start background trading tasks"""
    logger.info("Starting live trading system...")
    
    # Initialize trading components
    if initialize_trading_components():
        logger.info("Trading components initialized successfully")
    else:
        logger.warning("Running in demo mode - no live trading")
    
    # Start trading loop
    trading_thread = threading.Thread(target=trading_loop, daemon=True)
    trading_thread.start()
    
    logger.info("Live trading system started")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Live AI Crypto Trading Bot - Azure Deployment")
    logger.info("=" * 60)
    logger.info("Mode: LIVE TRADING with real money")
    logger.info("Symbols: BTCUSD, SOLUSD")
    logger.info("Risk: 10% per trade, 30% daily stop")
    logger.info("Platform: Azure Container Instances")
    logger.info("=" * 60)
    
    # Start background tasks
    start_background_tasks()
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8080))
    
    # Start Flask application
    logger.info(f"Starting Live Trading Bot on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


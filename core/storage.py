import json
import os
from datetime import datetime
import logging

class Storage:
    def __init__(self, data_dir="data", logger=None):
        self.data_dir = data_dir
        self.logger = logger or logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        self.orders_file = os.path.join(data_dir, "orders.json")
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.signals_file = os.path.join(data_dir, "signals.json")
        
    def log_order(self, symbol, entry_resp, sl_resp, tp_resp, signal, qty):
        """Log order placement"""
        try:
            order_data = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'quantity': qty,
                'signal': signal,
                'entry_order': entry_resp,
                'stop_loss_order': sl_resp,
                'take_profit_order': tp_resp
            }
            
            self._append_to_file(self.orders_file, order_data)
            self.logger.info(f"Logged order for {symbol}: {qty} @ {signal['entry']}")
            
        except Exception as e:
            self.logger.error(f"Error logging order: {e}")
    
    def log_trade_close(self, fill_event):
        """Log trade closure"""
        try:
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'symbol': fill_event['symbol'],
                'side': fill_event['side'],
                'role': fill_event.get('role'),
                'quantity': fill_event.get('quantity'),
                'price': fill_event.get('price'),
                'pnl': fill_event.get('pnl', 0.0),
                'client_order_id': fill_event.get('clientOrderId')
            }
            
            self._append_to_file(self.trades_file, trade_data)
            self.logger.info(f"Logged trade close: {fill_event['symbol']} PnL: {fill_event.get('pnl', 0.0)}")
            
        except Exception as e:
            self.logger.error(f"Error logging trade close: {e}")
    
    def log_signal(self, symbol, signal_data):
        """Log trading signal"""
        try:
            signal_entry = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'signal': signal_data
            }
            
            self._append_to_file(self.signals_file, signal_entry)
            
        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
    
    def _append_to_file(self, filename, data):
        """Append data to JSON file"""
        try:
            # Read existing data
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            # Append new data
            existing_data.append(data)
            
            # Write back to file
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error writing to {filename}: {e}")
    
    def get_recent_trades(self, limit=50):
        """Get recent trades"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
                return trades[-limit:] if len(trades) > limit else trades
            return []
            
        except Exception as e:
            self.logger.error(f"Error reading trades: {e}")
            return []
    
    def get_recent_orders(self, limit=50):
        """Get recent orders"""
        try:
            if os.path.exists(self.orders_file):
                with open(self.orders_file, 'r') as f:
                    orders = json.load(f)
                return orders[-limit:] if len(orders) > limit else orders
            return []
            
        except Exception as e:
            self.logger.error(f"Error reading orders: {e}")
            return []


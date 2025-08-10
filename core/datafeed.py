import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import logging

class DataFeed:
    def __init__(self, client, logger=None):
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        self.whale_cache = {}
        
    def get_klines(self, symbol, interval='5m', lookback=300):
        """Get historical kline data"""
        try:
            klines = self.client.get_historical_klines(
                symbol, interval, f"{lookback} minutes ago UTC"
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to numeric
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
                
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_equity_usd(self):
        """Get total account equity in USD"""
        try:
            account = self.client.get_account()
            total_usd = 0.0
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    if asset == 'USD' or asset == 'USDT':
                        total_usd += total
                    else:
                        # Convert to USD using current price
                        try:
                            ticker = self.client.get_symbol_ticker(symbol=f"{asset}USD")
                            price = float(ticker['price'])
                            total_usd += total * price
                        except:
                            # If USD pair doesn't exist, try USDT
                            try:
                                ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                                price = float(ticker['price'])
                                total_usd += total * price
                            except:
                                pass
                                
            return total_usd
            
        except Exception as e:
            self.logger.error(f"Error fetching equity: {e}")
            return 0.0
    
    def whale_flag(self, symbol, window_min=1, single_trade=250000, window_notional=1000000, imbalance=0.65):
        """Detect whale activity"""
        try:
            # Get recent trades
            trades = self.client.get_recent_trades(symbol=symbol, limit=1000)
            
            if not trades:
                return False
                
            now = datetime.now()
            window_start = now - timedelta(minutes=window_min)
            
            recent_trades = []
            total_volume = 0
            buy_volume = 0
            
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade['time'] / 1000)
                if trade_time >= window_start:
                    qty = float(trade['qty'])
                    price = float(trade['price'])
                    notional = qty * price
                    
                    recent_trades.append({
                        'notional': notional,
                        'is_buyer_maker': trade['isBuyerMaker']
                    })
                    
                    total_volume += notional
                    if not trade['isBuyerMaker']:  # Market buy
                        buy_volume += notional
                    
                    # Check for single large trade
                    if notional >= single_trade:
                        self.logger.info(f"Whale trade detected: {notional:,.2f} USD in {symbol}")
                        return True
            
            # Check for window volume threshold
            if total_volume >= window_notional:
                # Check for order imbalance
                if total_volume > 0:
                    buy_ratio = buy_volume / total_volume
                    if buy_ratio >= imbalance or buy_ratio <= (1 - imbalance):
                        self.logger.info(f"Whale activity detected: {total_volume:,.2f} USD volume with {buy_ratio:.2%} buy ratio in {symbol}")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting whale activity for {symbol}: {e}")
            return False


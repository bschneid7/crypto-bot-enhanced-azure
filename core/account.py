import logging
from typing import Dict, List

class Account:
    def __init__(self, client, logger=None):
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        self._precision_cache = {}
        
    def open_positions(self) -> List[Dict]:
        """Get current open positions"""
        try:
            account = self.client.get_account()
            positions = []
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0 and asset not in ['USD', 'USDT']:
                    positions.append({
                        'symbol': asset,
                        'quantity': total,
                        'free': free,
                        'locked': locked
                    })
                    
            return positions
            
        except Exception as e:
            self.logger.error(f"Error fetching positions: {e}")
            return []
    
    def open_orders(self, symbol=None) -> List[Dict]:
        """Get current open orders"""
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()
                
            return orders
            
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            return []
    
    def precision_map(self) -> Dict:
        """Get symbol precision information"""
        if self._precision_cache:
            return self._precision_cache
            
        try:
            exchange_info = self.client.get_exchange_info()
            precision_map = {}
            
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info['symbol']
                
                # Get quantity precision
                qty_precision = 0
                for filter_info in symbol_info['filters']:
                    if filter_info['filterType'] == 'LOT_SIZE':
                        step_size = float(filter_info['stepSize'])
                        qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))
                        break
                
                # Get price precision
                price_precision = symbol_info['quotePrecision']
                
                precision_map[symbol] = {
                    'qty': qty_precision,
                    'price': price_precision
                }
            
            self._precision_cache = precision_map
            return precision_map
            
        except Exception as e:
            self.logger.error(f"Error fetching precision map: {e}")
            return {}
    
    def get_balance(self, asset: str) -> Dict:
        """Get balance for specific asset"""
        try:
            account = self.client.get_account()
            
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return {
                        'asset': asset,
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    }
                    
            return {'asset': asset, 'free': 0.0, 'locked': 0.0, 'total': 0.0}
            
        except Exception as e:
            self.logger.error(f"Error fetching balance for {asset}: {e}")
            return {'asset': asset, 'free': 0.0, 'locked': 0.0, 'total': 0.0}


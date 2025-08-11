import uuid
import time
from typing import Optional

class LiveBroker:
    """
    Thin wrapper around your Binance.US client.
    - Places MARKET entry.
    - Immediately places separate STOP_LOSS_LIMIT and LIMIT_TP (emulated OCO).
    - Monitors and cancels sibling on fill.
    """
    def __init__(self, client, symbol_precisions):
        self.client = client
        self.symbol_precisions = symbol_precisions  # e.g., {"BTCUSD": {"qty": 6, "price": 2}}

    def _round(self, symbol, qty=None, price=None):
        p = self.symbol_precisions[symbol]
        rq = round(qty, p['qty']) if qty is not None else None
        rp = round(price, p['price']) if price is not None else None
        return rq, rp

    def place_market_entry(self, symbol: str, side: str, qty: float, client_id: Optional[str]=None):
        client_id = client_id or f"{symbol}-{side}-ENT-{uuid.uuid4().hex[:10]}"
        qty, _ = self._round(symbol, qty=qty)
        # Replace below with your client call for MARKET order:
        resp = self.client.create_order(symbol=symbol, side=side, type="MARKET", quantity=str(qty), newClientOrderId=client_id)
        return resp

    def place_stop_loss(self, symbol, side, qty, stop_price, limit_price, client_id=None):
        # Opposite side for exit
        exit_side = "SELL" if side == "BUY" else "BUY"
        qty, stop_price = self._round(symbol, qty=qty, price=stop_price)
        _, limit_price = self._round(symbol, price=limit_price)
        cid = client_id or f"{symbol}-{exit_side}-SL-{uuid.uuid4().hex[:8]}"
        # Replace with your STOP_LOSS_LIMIT call; on Binance.US it's typically type="STOP_LOSS_LIMIT"
        return self.client.create_order(symbol=symbol, side=exit_side, type="STOP_LOSS_LIMIT",
                                     quantity=str(qty), price=str(limit_price),
                                     stopPrice=str(stop_price), timeInForce="GTC",
                                     newClientOrderId=cid)

    def place_take_profit(self, symbol, side, qty, tp_price, client_id=None):
        exit_side = "SELL" if side == "BUY" else "BUY"
        qty, tp_price = self._round(symbol, qty=qty, price=tp_price)
        cid = client_id or f"{symbol}-{exit_side}-TP-{uuid.uuid4().hex[:8]}"
        return self.client.create_order(symbol=symbol, side=exit_side, type="LIMIT",
                                     quantity=str(qty), price=str(tp_price),
                                     timeInForce="GTC", newClientOrderId=cid)

    def cancel_order(self, symbol, order_id=None, client_order_id=None):
        return self.client.cancel_order(symbol=symbol, orderId=order_id, origClientOrderId=client_order_id)

    def reconcile_oco(self, symbol, filled_exit_client_id, sibling_hint="TP" ):
        """
        When stop or TP fills, cancel sibling.
        """
        try:
            # Ideally pass the sibling clientOrderId you stored.
            # Here we scan open orders and cancel the matching sibling type.
            open_orders = self.client.get_open_orders(symbol=symbol)
            for o in open_orders:
                if sibling_hint in (o.get('clientOrderId') or ''):
                    self.cancel_order(symbol, client_order_id=o['clientOrderId'])
        except Exception:
            pass

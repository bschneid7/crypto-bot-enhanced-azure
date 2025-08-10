import time
from core.signals import generate_signal
from core.sizing import aggressive_size
from core.risk import RiskEngine

class Engine:
    def __init__(self, broker, datafeed, account, params, storage, logger):
        self.broker = broker
        self.datafeed = datafeed  # must provide: get_klines(symbol, interval, lookback), get_equity_usd()
        self.account = account    # must provide: open_positions(), open_orders(), precision_map()
        self.params = params
        self.storage = storage    # persist signals/orders/trades
        self.logger = logger
        self.risk = RiskEngine(params)
        self.open_positions_cache = {}

    def tick(self, symbol):
        # 1) Risk gates
        equity = self.datafeed.get_equity_usd()
        ok, reason = self.risk.can_trade_now(time.time(), equity)
        if not ok: 
            self.logger.info(f"[{symbol}] trade halted: {reason}")
            return

        # 2) Already at position cap?
        if len(self.account.open_positions()) >=  self.params['limits']['max_trades_day']:
            return

        # 3) Build signal
        df = self.datafeed.get_klines(symbol, interval=self.params['timeframes']['trade'], lookback=300)
        whale_flag = self.datafeed.whale_flag(symbol, window_min=self.params['whales']['window_min'],
                                              single_trade=self.params['whales']['single_trade'],
                                              window_notional=self.params['whales']['window_notional'],
                                              imbalance=self.params['whales']['imbalance'])
        sig = generate_signal(df, whale_flag, self.params)
        if not sig:
            return

        # 4) Sizing
        qty, equity_managed = aggressive_size(
            total_equity_usd=equity,
            managed_fraction=self.params['account']['managed_fraction'],
            risk_per_trade=self.params['risk']['per_trade'],
            entry=sig['entry'],
            stop=sig['stop'],
            max_symbol_alloc=self.params['risk']['max_symbol_alloc'],
        )
        if qty <= 0:
            return

        # 5) Place live orders (market + exits)
        entry_resp = self.broker.place_market_entry(symbol, "BUY", qty)
        # Fill assumptions: use last price; for robust impl, poll order status
        sl_price = sig['stop']
        tp_price = sig['tp']
        # Use slightly worse stop limit to ensure trigger (e.g., limit a bit below stop)
        sl_limit = max(sl_price * 0.999, sl_price - 0.5 * sig['atr'])
        sl_resp = self.broker.place_stop_loss(symbol, "BUY", qty, stop_price=sl_price, limit_price=sl_limit)
        tp_resp = self.broker.place_take_profit(symbol, "BUY", qty, tp_price=tp_price)

        self.storage.log_order(symbol, entry_resp, sl_resp, tp_resp, sig, qty)

    def on_fill(self, fill_event):
        """
        Called by your websocket/streaming layer.
        If a stop or TP fills, cancel sibling and record PnL.
        """
        symbol = fill_event['symbol']
        side = fill_event['side']   # BUY/SELL
        role = fill_event.get('role')  # ENTRY/SL/TP
        if role in ('SL','TP'):
            # cancel sibling
            sibling_hint = 'TP' if role == 'SL' else 'SL'
            self.broker.reconcile_oco(symbol, filled_exit_client_id=fill_event.get('clientOrderId'),
                                      sibling_hint=sibling_hint)
            pnl = fill_event.get('pnl', 0.0)
            self.risk.record_trade_pnl(pnl)
            self.storage.log_trade_close(fill_event)


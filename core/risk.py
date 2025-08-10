import time
from collections import deque

class RiskEngine:
    def __init__(self, params):
        self.params = params
        self.day_start_equity = None
        self.day_loss_halt = False
        self.loss_streak = 0
        self.cooldown_until = 0
        self.daily_realized = 0.0
        self.trade_times = deque(maxlen=200)

    def on_new_day(self, equity):
        self.day_start_equity = equity
        self.day_loss_halt = False
        self.loss_streak = 0
        self.cooldown_until = 0
        self.daily_realized = 0.0

    def record_trade_pnl(self, pnl):
        self.daily_realized += pnl
        self.loss_streak = self.loss_streak + 1 if pnl < 0 else 0
        if self.loss_streak >= self.params['limits']['max_consecutive_losses']:
            self.cooldown_until = time.time() + 60 * self.params['cooldown_minutes_after_loss_streak']

    def can_trade_now(self, now_ts, live_equity):
        if self.day_start_equity is None:
            self.on_new_day(live_equity)

        # Daily drawdown
        dd = 0.0
        if self.day_start_equity > 0:
            dd = (self.day_start_equity - live_equity) / self.day_start_equity
        if dd >= self.params['risk']['daily_stop']:
            self.day_loss_halt = True

        if self.day_loss_halt:
            return False, f"Daily stop hit ({dd:.1%})."

        if now_ts < self.cooldown_until:
            return False, "Cooling down after loss streak."

        return True, ""


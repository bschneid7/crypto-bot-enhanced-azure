def aggressive_size(total_equity_usd, managed_fraction, risk_per_trade, entry, stop, max_symbol_alloc):
    equity_managed = total_equity_usd * managed_fraction
    per_unit_risk = max(entry - stop, 1e-6)
    risk_dollars = equity_managed * risk_per_trade
    qty_by_risk = risk_dollars / per_unit_risk
    qty_by_alloc = (equity_managed * max_symbol_alloc) / entry
    qty = max(0.0, min(qty_by_risk, qty_by_alloc))
    return round(qty, 6), equity_managed


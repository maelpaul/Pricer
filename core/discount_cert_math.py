"""
Discount Certificate pricing.
Replication: DC = PV(Underlying) - Call(K=Cap)
"""

import numpy as np
from core.black_scholes import bs_price


def dc_price(S, cap, T, r, q, sigma, parity=1):
    """
    Discount Certificate price.
    DC = PV(S) - Call(K=Cap)
    """
    pv_underlying = S * np.exp(-q * T)
    call_at_cap = bs_price(S, cap, T, r, q, sigma, "call")
    price = (pv_underlying - call_at_cap) / parity
    return {
        "price": price,
        "pv_underlying": pv_underlying,
        "call_at_cap": call_at_cap,
    }


def dc_metrics(S, cap, T, r, q, sigma, parity=1):
    """Compute all Discount Certificate key metrics."""
    result = dc_price(S, cap, T, r, q, sigma, parity)
    price = result["price"]

    # Discount vs current stock price
    discount_pct = (S - price * parity) / S * 100 if S > 0 else 0.0

    # Max payoff = cap / parity
    max_payoff = cap / parity

    # Max return
    max_return = (max_payoff / price - 1) * 100 if price > 0 else 0.0

    # Breakeven = DC price * parity (stock must be above this)
    breakeven = price * parity

    # Sideways return: if stock stays flat, payoff = min(S, cap) / parity
    sideways_payoff = min(S, cap) / parity
    sideways_return = (sideways_payoff / price - 1) * 100 if price > 0 else 0.0

    return {
        **result,
        "discount_pct": discount_pct,
        "max_payoff": max_payoff,
        "max_return": max_return,
        "breakeven": breakeven,
        "sideways_return": sideways_return,
    }


def dc_payoff(S_range, cap, parity=1):
    """Payoff at maturity for Discount Certificate."""
    return np.minimum(S_range, cap) / parity


def dc_pnl(S_range, cap, entry_price, parity=1):
    """P&L at maturity."""
    payoff = dc_payoff(S_range, cap, parity)
    return payoff - entry_price


def dc_sensitivity_vol(S, cap, T, r, q, parity=1, vol_min=0.05, vol_max=0.60, n=50):
    """DC price and discount vs volatility."""
    vols = np.linspace(vol_min, vol_max, n)
    prices = []
    discounts = []
    for v in vols:
        m = dc_metrics(S, cap, T, r, q, v, parity)
        prices.append(m["price"])
        discounts.append(m["discount_pct"])
    return vols, prices, discounts


def dc_sensitivity_cap(S, T, r, q, sigma, parity=1, cap_min=None, cap_max=None, n=50):
    """DC price and max return vs cap level."""
    if cap_min is None:
        cap_min = S * 0.8
    if cap_max is None:
        cap_max = S * 1.5
    caps = np.linspace(cap_min, cap_max, n)
    prices = []
    max_returns = []
    for c in caps:
        m = dc_metrics(S, c, T, r, q, sigma, parity)
        prices.append(m["price"])
        max_returns.append(m["max_return"])
    return caps, prices, max_returns

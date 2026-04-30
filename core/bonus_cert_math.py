"""
Bonus Certificate pricing.

Replication:
  BC = Zero-coupon bond (par) + Down-and-Out Put(K=Bonus, B=Barrier) [+ optional cap via short call]

If barrier is NOT breached: payoff = max(Bonus, S_T)  (or min(max(Bonus, S_T), Cap) if capped)
If barrier IS breached: payoff = S_T  (or min(S_T, Cap) if capped)
"""

import numpy as np
from scipy.stats import norm
from core.black_scholes import bs_price


def _down_and_out_put(S, K, B, T, r, q, sigma):
    """
    Closed-form price for a European Down-and-Out Put option.
    Valid for B < K and B < S.
    Uses the reflection principle / barrier option formula.
    """
    if T <= 0 or sigma <= 0:
        if S > B:
            return max(K - S, 0.0)
        return 0.0

    if S <= B:
        return 0.0

    lam = (r - q + 0.5 * sigma**2) / (sigma**2)
    sqrt_T = sigma * np.sqrt(T)

    x1 = np.log(S / K) / sqrt_T + lam * sqrt_T
    x2 = np.log(S / B) / sqrt_T + lam * sqrt_T
    y1 = np.log(B**2 / (S * K)) / sqrt_T + lam * sqrt_T
    y2 = np.log(B / S) / sqrt_T + lam * sqrt_T

    # Standard put price
    put_vanilla = bs_price(S, K, T, r, q, sigma, "put")

    # Down-and-In Put
    di_put = (
        -S * np.exp(-q * T) * norm.cdf(-x1)
        + K * np.exp(-r * T) * norm.cdf(-x1 + sqrt_T)
        + S * np.exp(-q * T) * (B / S) ** (2 * lam) * (norm.cdf(y1) - norm.cdf(y2))
        - K * np.exp(-r * T) * (B / S) ** (2 * lam - 2) * (
            norm.cdf(y1 - sqrt_T) - norm.cdf(y2 - sqrt_T)
        )
    )

    # Down-and-Out Put = Vanilla Put - Down-and-In Put
    do_put = put_vanilla - di_put
    return max(do_put, 0.0)


def bc_price(S, bonus_level, barrier, T, r, q, put_vol, call_vol=None,
             cap_enabled=False, cap_level=None, parity=1):
    """
    Bonus Certificate price.

    BC = PV(S) + Down-and-Out Put(K=Bonus, B=Barrier)
    If capped: BC -= Call(K=Cap)
    """
    # Forward / PV of underlying
    pv_underlying = S * np.exp(-q * T)

    # Down-and-Out Put
    do_put = _down_and_out_put(S, bonus_level, barrier, T, r, q, put_vol)

    price = pv_underlying + do_put

    # If capped, subtract call at cap level
    call_at_cap = 0.0
    if cap_enabled and cap_level is not None:
        _call_vol = call_vol if call_vol is not None else put_vol
        call_at_cap = bs_price(S, cap_level, T, r, q, _call_vol, "call")
        price -= call_at_cap

    price /= parity

    return {
        "price": price,
        "pv_underlying": pv_underlying,
        "do_put": do_put,
        "call_at_cap": call_at_cap,
    }


def bc_metrics(S, bonus_level, barrier, T, r, q, put_vol, call_vol=None,
               cap_enabled=False, cap_level=None, parity=1):
    """Compute all Bonus Certificate key metrics."""
    result = bc_price(S, bonus_level, barrier, T, r, q, put_vol, call_vol,
                      cap_enabled, cap_level, parity)
    price = result["price"]

    # Discount/Premium vs stock
    premium_pct = (price * parity / S - 1) * 100 if S > 0 else 0.0

    # Bonus return: if barrier not breached
    bonus_payoff = bonus_level / parity
    if cap_enabled and cap_level is not None:
        bonus_payoff = min(bonus_level, cap_level) / parity
    bonus_return = (bonus_payoff / price - 1) * 100 if price > 0 else 0.0

    # Max return
    if cap_enabled and cap_level is not None:
        max_payoff = cap_level / parity
    else:
        max_payoff = float("inf")
    max_return = (max_payoff / price - 1) * 100 if price > 0 and max_payoff != float("inf") else float("inf")

    return {
        **result,
        "premium_pct": premium_pct,
        "bonus_return": bonus_return,
        "max_return": max_return,
    }


def bc_payoff(S_range, S0, bonus_level, barrier, cap_enabled=False,
              cap_level=None, parity=1, barrier_breached=True):
    """
    Payoff at maturity.
    barrier_breached=True: worst case (barrier was hit) -> payoff = S_T / parity
    barrier_breached=False: barrier NOT hit -> payoff = max(Bonus, S_T) / parity
    """
    payoffs = []
    for s in S_range:
        if barrier_breached:
            p = s / parity
        else:
            p = max(bonus_level, s) / parity
        if cap_enabled and cap_level is not None:
            p = min(p, cap_level / parity)
        payoffs.append(p)
    return np.array(payoffs)


def bc_sensitivity_vol(S, bonus_level, barrier, T, r, q, call_vol=None,
                       cap_enabled=False, cap_level=None, parity=1,
                       vol_min=0.05, vol_max=0.60, n=50):
    """BC price and D&O put vs volatility."""
    vols = np.linspace(vol_min, vol_max, n)
    prices = []
    do_puts = []
    for v in vols:
        _cv = call_vol if call_vol is not None else v
        result = bc_price(S, bonus_level, barrier, T, r, q, v, _cv,
                          cap_enabled, cap_level, parity)
        prices.append(result["price"])
        do_puts.append(result["do_put"])
    return vols, prices, do_puts


def bc_sensitivity_time(S, bonus_level, barrier, r, q, put_vol, call_vol=None,
                        cap_enabled=False, cap_level=None, parity=1,
                        t_min=0.05, t_max=3.0, n=50):
    """BC price and D&O put vs time to maturity."""
    times = np.linspace(t_min, t_max, n)
    prices = []
    do_puts = []
    for t in times:
        result = bc_price(S, bonus_level, barrier, t, r, q, put_vol, call_vol,
                          cap_enabled, cap_level, parity)
        prices.append(result["price"])
        do_puts.append(result["do_put"])
    return times, prices, do_puts

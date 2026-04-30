"""
Turbo (Open-End Knock-Out) certificate pricing.
"""

import numpy as np


def turbo_price(S, K, parity, turbo_type="long"):
    """
    Turbo price.
    Long: (S - K) / parity
    Short: (K - S) / parity
    """
    if turbo_type == "long":
        return max((S - K) / parity, 0.0)
    else:
        return max((K - S) / parity, 0.0)


def leverage(S, K, parity, turbo_type="long"):
    """Leverage = S / (Turbo_Price * Parity)."""
    tp = turbo_price(S, K, parity, turbo_type)
    if tp <= 0:
        return float("inf")
    return S / (tp * parity)


def distance_to_barrier(S, B):
    """Distance to barrier as percentage."""
    if S == 0:
        return 0.0
    return abs(S - B) / S


def daily_funding_cost(K, financing_rate, parity):
    """Daily funding cost per certificate."""
    return K * (financing_rate / 365) / parity


def strike_drift(K, financing_rate, days):
    """Strike after N days of financing cost accrual."""
    return K * (1 + financing_rate * days / 365)


def turbo_metrics(S, K, B, parity, financing_rate, lots=1.0, mult=100, turbo_type="long"):
    """Compute all turbo metrics."""
    tp = turbo_price(S, K, parity, turbo_type)
    lev = leverage(S, K, parity, turbo_type)
    dist = distance_to_barrier(S, B)
    daily_fund = daily_funding_cost(K, financing_rate, parity)
    notional = lots * mult

    return {
        "turbo_price": tp,
        "leverage": lev,
        "distance_to_barrier": dist,
        "daily_funding_cost": daily_fund,
        "initial_delta_cash": tp * parity * notional / parity,  # = tp * notional
        "leveraged_delta_cash": S * notional / parity,
        "equivalent_underlying": notional / parity,
    }


def financing_simulation(S, K, B, parity, financing_rate, holding_days, turbo_type="long"):
    """Simulate strike drift and value erosion over holding period."""
    days = np.arange(0, holding_days + 1)
    k_series = K * (1 + financing_rate * days / 365)
    tp_series = np.array([turbo_price(S, k, parity, turbo_type) for k in k_series])
    erosion = tp_series[0] - tp_series

    k_end = k_series[-1]
    tp_end = tp_series[-1]
    k_change = k_end - K
    value_erosion = tp_series[0] - tp_end

    return {
        "days": days,
        "k_series": k_series,
        "tp_series": tp_series,
        "erosion": erosion,
        "k_today": K,
        "k_end": k_end,
        "k_change": k_change,
        "tp_end": tp_end,
        "value_erosion": value_erosion,
    }


def payoff_at_maturity(S_range, K, B, parity, turbo_type="long"):
    """Payoff at current time (intrinsic value) for a range of spot prices."""
    payoffs = []
    for s in S_range:
        if turbo_type == "long":
            if s <= B:
                payoffs.append(0.0)
            else:
                payoffs.append(max((s - K) / parity, 0.0))
        else:
            if s >= B:
                payoffs.append(0.0)
            else:
                payoffs.append(max((K - s) / parity, 0.0))
    return np.array(payoffs)

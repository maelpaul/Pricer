"""
Black-Scholes pricing engine with full Greeks suite.
"""

import numpy as np
from scipy.stats import norm


def d1(S, K, T, r, q, sigma):
    """Compute d1 of the Black-Scholes formula."""
    if T <= 0 or sigma <= 0:
        return 0.0
    return (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))


def d2(S, K, T, r, q, sigma):
    """Compute d2 of the Black-Scholes formula."""
    return d1(S, K, T, r, q, sigma) - sigma * np.sqrt(T)


def forward_price(S, r, q, T):
    """Forward price."""
    return S * np.exp((r - q) * T)


def bs_price(S, K, T, r, q, sigma, option_type="call"):
    """Black-Scholes European option price."""
    if T <= 0:
        if option_type == "call":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)
    if sigma <= 0:
        if option_type == "call":
            return max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
        else:
            return max(K * np.exp(-r * T) - S * np.exp(-q * T), 0.0)

    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)

    if option_type == "call":
        return S * np.exp(-q * T) * norm.cdf(_d1) - K * np.exp(-r * T) * norm.cdf(_d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-_d2) - S * np.exp(-q * T) * norm.cdf(-_d1)


# ---------------------------------------------------------------------------
# Unit Greeks
# ---------------------------------------------------------------------------

def delta(S, K, T, r, q, sigma, option_type="call"):
    """Delta: dV/dS."""
    if T <= 0 or sigma <= 0:
        if option_type == "call":
            return 1.0 if S > K else (0.5 if S == K else 0.0)
        else:
            return -1.0 if S < K else (-0.5 if S == K else 0.0)
    _d1 = d1(S, K, T, r, q, sigma)
    if option_type == "call":
        return np.exp(-q * T) * norm.cdf(_d1)
    else:
        return np.exp(-q * T) * (norm.cdf(_d1) - 1)


def gamma(S, K, T, r, q, sigma):
    """Gamma: d²V/dS² (same for call and put)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    return np.exp(-q * T) * norm.pdf(_d1) / (S * sigma * np.sqrt(T))


def theta(S, K, T, r, q, sigma, option_type="call"):
    """Theta: -dV/dT (annualized, negative for long positions).

    Convention: Theta < 0 means the option loses value as time passes.
    Formula from Hull (10th ed.).
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)

    # Common term: time-decay component
    term1 = -S * np.exp(-q * T) * norm.pdf(_d1) * sigma / (2 * np.sqrt(T))
    if option_type == "call":
        return (term1
                + q * S * np.exp(-q * T) * norm.cdf(_d1)
                - r * K * np.exp(-r * T) * norm.cdf(_d2))
    else:
        return (term1
                - q * S * np.exp(-q * T) * norm.cdf(-_d1)
                + r * K * np.exp(-r * T) * norm.cdf(-_d2))


def vega(S, K, T, r, q, sigma):
    """Vega: dV/dσ (same for call and put). Per 1 unit of sigma."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    return S * np.exp(-q * T) * norm.pdf(_d1) * np.sqrt(T)


def rho(S, K, T, r, q, sigma, option_type="call"):
    """Rho: dV/dr. Per 1 unit of r."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return K * T * np.exp(-r * T) * norm.cdf(_d2)
    else:
        return -K * T * np.exp(-r * T) * norm.cdf(-_d2)


def charm(S, K, T, r, q, sigma, option_type="call"):
    """Charm: -dDelta/dT.

    Measures how delta changes as time to maturity decreases.
    Negative charm for ATM call means delta drifts down as time passes.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)
    sqrtT = np.sqrt(T)

    pdf_d1 = norm.pdf(_d1)
    bracket = (2 * (r - q) * T - _d2 * sigma * sqrtT) / (2 * T * sigma * sqrtT)
    charm_val = -np.exp(-q * T) * pdf_d1 * bracket

    if option_type == "call":
        return charm_val + q * np.exp(-q * T) * norm.cdf(_d1)
    else:
        return charm_val - q * np.exp(-q * T) * norm.cdf(-_d1)


def vanna(S, K, T, r, q, sigma):
    """Vanna: d²V/(dS dσ) = dDelta/dσ. Same for call and put."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)
    v = vega(S, K, T, r, q, sigma)
    if v == 0:
        return 0.0
    return -np.exp(-q * T) * norm.pdf(_d1) * _d2 / sigma


def volga(S, K, T, r, q, sigma):
    """Volga (Vomma): d²V/dσ². Same for call and put."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)
    v = vega(S, K, T, r, q, sigma)
    return v * _d1 * _d2 / sigma


def speed(S, K, T, r, q, sigma):
    """Speed: dGamma/dS."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    g = gamma(S, K, T, r, q, sigma)
    return -g / S * (_d1 / (sigma * np.sqrt(T)) + 1)


def color(S, K, T, r, q, sigma):
    """Color: dGamma/dT."""
    if T <= 0 or sigma <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, q, sigma)
    _d2 = _d1 - sigma * np.sqrt(T)
    return -np.exp(-q * T) * norm.pdf(_d1) / (2 * S * T * sigma * np.sqrt(T)) * (
        2 * q * T + 1 + _d1 * (2 * (r - q) * T - _d2 * sigma * np.sqrt(T))
        / (sigma * np.sqrt(T))
    )


# ---------------------------------------------------------------------------
# Cash Greeks (position-level)
# ---------------------------------------------------------------------------

def cash_greeks(S, K, T, r, q, sigma, lots=1.0, mult=100, option_type="call"):
    """Compute all cash (position-level) Greeks."""
    _delta = delta(S, K, T, r, q, sigma, option_type)
    _gamma = gamma(S, K, T, r, q, sigma)
    _theta = theta(S, K, T, r, q, sigma, option_type)
    _vega = vega(S, K, T, r, q, sigma)
    _rho = rho(S, K, T, r, q, sigma, option_type)
    _charm = charm(S, K, T, r, q, sigma, option_type)
    _vanna = vanna(S, K, T, r, q, sigma)

    notional = lots * mult

    return {
        "cash_delta": _delta * notional * S,
        "delta_hedge": _delta * notional,  # shares
        "gamma_1pct": _gamma * S**2 / 100 * notional,
        "theta_day": _theta / 365 * notional,
        "vega_1pct": _vega * 0.01 * notional,
        "charm_day": _charm / 365 * S * notional,
        "vanna_1pct": _vanna * 0.01 * S * notional,
        "rho_1pct": _rho * 0.01 * notional,
    }


def delta_t1d(S, K, T, r, q, sigma, lots=1.0, mult=100, option_type="call"):
    """Change in delta hedge for 1 day passage."""
    if T <= 1 / 365:
        return 0.0
    d_now = delta(S, K, T, r, q, sigma, option_type)
    d_tmr = delta(S, K, T - 1 / 365, r, q, sigma, option_type)
    return (d_tmr - d_now) * lots * mult


# ---------------------------------------------------------------------------
# Full unit Greeks dict for display
# ---------------------------------------------------------------------------

def unit_greeks(S, K, T, r, q, sigma, option_type="call"):
    """Return a dict of all unit Greeks for display table."""
    return {
        "Delta": delta(S, K, T, r, q, sigma, option_type),
        "Gamma": gamma(S, K, T, r, q, sigma),
        "Theta /day": theta(S, K, T, r, q, sigma, option_type) / 365,
        "Vega /1%": vega(S, K, T, r, q, sigma) / 100,
        "Rho /1%": rho(S, K, T, r, q, sigma, option_type) / 100,
        "Charm /day": charm(S, K, T, r, q, sigma, option_type) / 365,
        "Vanna /1%": vanna(S, K, T, r, q, sigma) / 100,
        "Volga /1%": volga(S, K, T, r, q, sigma) / 100,
    }


"""
Bond pricing, duration, convexity, and risk metrics.
"""

import numpy as np
from scipy import optimize


def bond_price(face, coupon_rate, ytm, maturity, freq=2, settlement_days=0):
    """
    Compute the dirty price of a bond.

    Parameters
    ----------
    face : float – Face/par value
    coupon_rate : float – Annual coupon rate (decimal, e.g. 0.05)
    ytm : float – Yield to maturity (decimal)
    maturity : float – Years to maturity
    freq : int – Coupon frequency per year (1, 2, or 4)
    settlement_days : int – Settlement days offset

    Returns
    -------
    dict with clean_price, dirty_price, accrued_interest, etc.
    """
    coupon = face * coupon_rate / freq
    n_periods = int(round(maturity * freq))
    y = ytm / freq

    if n_periods <= 0:
        return {
            "dirty_price": face,
            "clean_price": face,
            "accrued_interest": 0.0,
        }

    # Settlement fraction (fraction of period elapsed)
    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0

    # PV of cash flows
    pv = 0.0
    for i in range(1, n_periods + 1):
        t = i - settl_frac
        if y == 0:
            pv += coupon
        else:
            pv += coupon / (1 + y) ** t

    # PV of principal
    t_last = n_periods - settl_frac
    if y == 0:
        pv += face
    else:
        pv += face / (1 + y) ** t_last

    # Accrued interest
    accrued = coupon * settl_frac

    dirty_price = pv
    clean_price = dirty_price - accrued

    return {
        "dirty_price": dirty_price,
        "clean_price": clean_price,
        "accrued_interest": accrued,
    }


def duration_convexity(face, coupon_rate, ytm, maturity, freq=2, settlement_days=0):
    """
    Compute Macaulay duration, modified duration, and convexity.
    """
    coupon = face * coupon_rate / freq
    n_periods = int(round(maturity * freq))
    y = ytm / freq

    if n_periods <= 0:
        return {"mac_duration": 0.0, "mod_duration": 0.0, "convexity": 0.0}

    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0

    price = 0.0
    dur_sum = 0.0
    conv_sum = 0.0

    for i in range(1, n_periods + 1):
        t = i - settl_frac
        cf = coupon
        if i == n_periods:
            cf += face
        if y == 0:
            pv_cf = cf
        else:
            pv_cf = cf / (1 + y) ** t
        price += pv_cf
        dur_sum += t * pv_cf
        conv_sum += t * (t + 1) * pv_cf

    if price == 0:
        return {"mac_duration": 0.0, "mod_duration": 0.0, "convexity": 0.0}

    mac_duration = dur_sum / price / freq  # in years
    mod_duration = mac_duration / (1 + y)
    convexity = conv_sum / (price * (1 + y) ** 2) / freq**2

    return {
        "mac_duration": mac_duration,
        "mod_duration": mod_duration,
        "convexity": convexity,
    }


def dv01(face, coupon_rate, ytm, maturity, freq=2, settlement_days=0):
    """DV01: dollar value of 1 basis point."""
    bp = 0.0001
    p_up = bond_price(face, coupon_rate, ytm + bp, maturity, freq, settlement_days)["dirty_price"]
    p_dn = bond_price(face, coupon_rate, ytm - bp, maturity, freq, settlement_days)["dirty_price"]
    return abs(p_dn - p_up) / 2


def pv01(face, coupon_rate, ytm, maturity, freq, settlement_days, notional, shift_bp=1.0):
    """PV01: P&L for notional and shift."""
    bp = shift_bp * 0.0001
    p_base = bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days)["dirty_price"]
    p_shift = bond_price(face, coupon_rate, ytm + bp, maturity, freq, settlement_days)["dirty_price"]
    return (p_shift - p_base) / face * notional


def price_vs_yield_data(face, coupon_rate, maturity, freq=2, settlement_days=0,
                        ytm_min=0.005, ytm_max=0.20, n_points=100,
                        callable_on=False, call_price=None, call_date_years=None,
                        putable_on=False, put_price=None, put_date_years=None, rate_vol=0.0):
    """Generate data for Price vs Yield chart."""
    ytms = np.linspace(ytm_min, ytm_max, n_points)
    prices = []
    call_prices = [] if callable_on else None
    put_prices = [] if putable_on else None
    
    for y in ytms:
        p = bond_price(face, coupon_rate, y, maturity, freq, settlement_days)
        prices.append(p["dirty_price"])
        if callable_on:
            cp = callable_bond_price(face, coupon_rate, y, maturity, freq, settlement_days, call_price, call_date_years, rate_vol)
            call_prices.append(cp["callable_price"])
        if putable_on:
            pp = putable_bond_price(face, coupon_rate, y, maturity, freq, settlement_days, put_price, put_date_years, rate_vol)
            put_prices.append(pp["putable_price"])
    if callable_on or putable_on:
        return ytms, prices, call_prices, put_prices
    return ytms, prices


def cashflow_pv_data(face, coupon_rate, ytm, maturity, freq=2, settlement_days=0):
    """Generate PV of each cash flow for bar chart."""
    coupon = face * coupon_rate / freq
    n_periods = int(round(maturity * freq))
    y = ytm / freq

    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0

    periods = []
    coupon_pvs = []
    principal_pvs = []

    for i in range(1, n_periods + 1):
        t = i - settl_frac
        t_years = i / freq
        if y == 0:
            cpn_pv = coupon
        else:
            cpn_pv = coupon / (1 + y) ** t

        if i == n_periods:
            if y == 0:
                prin_pv = face
            else:
                prin_pv = face / (1 + y) ** t
        else:
            prin_pv = 0.0

        periods.append(t_years)
        coupon_pvs.append(cpn_pv)
        principal_pvs.append(prin_pv)

    return periods, coupon_pvs, principal_pvs


def yield_to_call(face, coupon_rate, current_price, settlement_days, freq, call_price, call_date_years):
    coupon = face * coupon_rate / freq
    n_periods = int(round(call_date_years * freq))
    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0

    def objective(y):
        y_per_period = y / freq
        pv = 0.0
        for i in range(1, n_periods + 1):
            t = i - settl_frac
            pv += coupon / (1 + y_per_period) ** t
            if i == n_periods:
                pv += call_price / (1 + y_per_period) ** t
        
        # Accrued interest is subtracted to get clean price, 
        # but current_price should be the DIRTY price for this calculation.
        return pv - current_price
        
    try:
        res = optimize.newton(objective, 0.05)
        return res
    except:
        return 0.0

def yield_to_put(face, coupon_rate, current_price, settlement_days, freq, put_price, put_date_years):
    coupon = face * coupon_rate / freq
    n_periods = int(round(put_date_years * freq))
    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0

    def objective(y):
        y_per_period = y / freq
        pv = 0.0
        for i in range(1, n_periods + 1):
            t = i - settl_frac
            pv += coupon / (1 + y_per_period) ** t
            if i == n_periods:
                pv += put_price / (1 + y_per_period) ** t
        return pv - current_price
        
    try:
        res = optimize.newton(objective, 0.05)
        return res
    except:
        return 0.0

def binomial_rate_tree(ytm, rate_vol, maturity, freq):
    n_steps = int(round(maturity * freq))
    dt = 1.0 / freq
    r0 = ytm / freq
    u = np.exp(rate_vol * np.sqrt(dt))
    d = 1 / u
    tree = []
    for i in range(n_steps + 1):
        rates = np.zeros(i + 1)
        for j in range(i + 1):
            rates[j] = r0 * (u ** j) * (d ** (i - j))
        tree.append(rates)
    return tree

def option_adjusted_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                               callable_on=False, call_price=None, call_date_years=None,
                               putable_on=False, put_price=None, put_date_years=None,
                               rate_vol=0.0):
    n_steps = int(round(maturity * freq))
    dt = 1.0 / freq
    coupon = face * coupon_rate / freq
    
    call_step = int(round(call_date_years * freq)) if callable_on and call_date_years is not None else n_steps + 1
    put_step = int(round(put_date_years * freq)) if putable_on and put_date_years is not None else n_steps + 1
    
    # If volatility is 0, add a tiny bit to avoid flat tree issues, or just use 0.
    vol = max(rate_vol, 0.0001)
    tree = binomial_rate_tree(ytm, vol, maturity, freq)
    
    values = np.ones(n_steps + 1) * (face + coupon)
    straight_values = np.ones(n_steps + 1) * (face + coupon)
    tree_values = [values.copy()]
    
    for i in range(n_steps - 1, -1, -1):
        rates = tree[i]
        new_values = np.zeros(i + 1)
        new_straight = np.zeros(i + 1)
        
        for j in range(i + 1):
            expected_val = 0.5 * (values[j] + values[j+1])
            node_val = expected_val / (1 + rates[j])
            
            exp_straight = 0.5 * (straight_values[j] + straight_values[j+1])
            node_straight = exp_straight / (1 + rates[j])
            
            if i > 0:
                node_val += coupon
                node_straight += coupon
            
            if callable_on and i >= call_step:
                node_val = min(node_val, call_price + (coupon if i > 0 else 0))
            if putable_on and i >= put_step:
                node_val = max(node_val, put_price + (coupon if i > 0 else 0))
                
            new_values[j] = node_val
            new_straight[j] = node_straight
            
        values = new_values
        straight_values = new_straight
        tree_values.append(values.copy())
        
    period_days = 365.0 / freq
    settl_frac = (settlement_days % period_days) / period_days if period_days > 0 else 0.0
    
    if settl_frac > 0:
        dirty_price = values[0] * (1 + ytm/freq)**settl_frac
        straight_dirty = straight_values[0] * (1 + ytm/freq)**settl_frac
    else:
        dirty_price = values[0]
        straight_dirty = straight_values[0]
        
    accrued = coupon * settl_frac
    clean_price = dirty_price - accrued
    
    return {
        "dirty_price": dirty_price,
        "clean_price": clean_price,
        "straight_tree_price": straight_dirty,
        "accrued_interest": accrued,
        "tree_rates": tree,
        "tree_values": list(reversed(tree_values))
    }

def callable_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                        call_price, call_date_years, rate_vol=0.0):
    oa = option_adjusted_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                                    callable_on=True, call_price=call_price, call_date_years=call_date_years,
                                    rate_vol=rate_vol)
    return {
        "straight_price": oa["straight_tree_price"],
        "callable_price": oa["dirty_price"],
        "tree": oa["tree_values"]
    }

def putable_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                        put_price, put_date_years, rate_vol=0.0):
    oa = option_adjusted_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                                    putable_on=True, put_price=put_price, put_date_years=put_date_years,
                                    rate_vol=rate_vol)
    return {
        "straight_price": oa["straight_tree_price"],
        "putable_price": oa["dirty_price"],
        "tree": oa["tree_values"]
    }

def callable_putable_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                                call_price, call_date_years, put_price, put_date_years, rate_vol=0.0):
    oa = option_adjusted_bond_price(face, coupon_rate, ytm, maturity, freq, settlement_days,
                                    callable_on=True, call_price=call_price, call_date_years=call_date_years,
                                    putable_on=True, put_price=put_price, put_date_years=put_date_years,
                                    rate_vol=rate_vol)
    return {
        "straight_price": oa["straight_tree_price"],
        "price": oa["dirty_price"],
        "tree": oa["tree_values"]
    }

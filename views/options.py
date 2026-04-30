"""
Options page — Black-Scholes pricer with full Greeks suite.
"""

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from core.black_scholes import (
    bs_price, forward_price, delta, gamma, theta, vega, rho,
    charm, vanna, volga, speed, color,
    cash_greeks, delta_t1d, unit_greeks,
)
from utils.charts import (
    greek_vs_spot_by_vol, greek_vs_time_by_moneyness, COLORS,
)
import plotly.graph_objects as go


def render_sidebar():
    """Render the Options sidebar inputs and return parameters."""
    st.sidebar.markdown("#### Parameters")
    st.sidebar.caption("Market & Contract")

    S = st.sidebar.number_input("Spot (S)", value=100.00, step=1.00, format="%.2f")
    K = st.sidebar.number_input("Strike (K)", value=100.00, step=1.00, format="%.2f")

    mat_date = st.sidebar.date_input("Maturity", value=datetime.now().date() + timedelta(days=365))
    T = max((mat_date - datetime.now().date()).days / 365.25, 0.0001)
    st.sidebar.caption(f"T = {T:.4f} y")

    st.sidebar.markdown("---")
    col_r, col_q = st.sidebar.columns(2)
    r_pct = col_r.number_input("r %", value=5.00, step=0.10, format="%.2f")
    q_pct = col_q.number_input("q %", value=2.00, step=0.10, format="%.2f")

    col_repo, col_sig = st.sidebar.columns(2)
    repo_pct = col_repo.number_input("repo %", value=0.00, step=0.10, format="%.2f")
    sigma_pct = col_sig.number_input("σ %", value=20.00, step=0.50, format="%.2f")

    st.sidebar.markdown("---")
    st.sidebar.caption("Position")
    option_type = st.sidebar.radio("Type", ["Call", "Put"], horizontal=True)
    col_lots, col_mult = st.sidebar.columns(2)
    lots = col_lots.number_input("Lots", value=1.0, step=1.0, format="%.1f")
    mult = col_mult.number_input("Mult.", value=100, step=1)

    r = r_pct / 100
    q = q_pct / 100
    sigma = sigma_pct / 100

    return {
        "S": S, "K": K, "T": T, "r": r, "q": q, "sigma": sigma,
        "lots": lots, "mult": mult, "sigma_pct": sigma_pct,
        "option_type": option_type.lower(),
    }


def render(params):
    """Render the Options main content area."""
    S = params["S"]
    K = params["K"]
    T = params["T"]
    r = params["r"]
    q = params["q"]
    sigma = params["sigma"]
    lots = params["lots"]
    mult = int(params["mult"])
    otype = params["option_type"]

    # ── PRICING ──────────────────────────────────────────────
    st.markdown("#### PRICING")
    price = bs_price(S, K, T, r, q, sigma, otype)
    fwd = forward_price(S, r, q, T)
    cg = cash_greeks(S, K, T, r, q, sigma, lots, mult, otype)
    dt1d = delta_t1d(S, K, T, r, q, sigma, lots, mult, otype)

    cols = st.columns(5)
    cols[0].metric("BS PRICE", f"{price:.4f}")
    cols[1].metric("FORWARD", f"{fwd:.4f}")
    cols[2].metric("CASH DELTA", f"{cg['cash_delta']:,.2f}")
    cols[3].metric("DELTA HEDGE", f"{cg['delta_hedge']:.1f} shrs")
    cols[4].metric("Δ T+1D", f"{dt1d:.2f} shrs/day")

    # ── CASH GREEKS ──────────────────────────────────────────
    st.markdown("#### CASH GREEKS")
    cols2 = st.columns(6)
    cols2[0].metric("GAMMA / 1%", f"{cg['gamma_1pct']:.2f}")
    cols2[1].metric("THETA / DAY", f"{cg['theta_day']:.2f}")
    cols2[2].metric("VEGA / 1%", f"{cg['vega_1pct']:.2f}")
    cols2[3].metric("CHARM / DAY", f"{cg['charm_day']:.2f}")
    cols2[4].metric("VANNA / 1%", f"{cg['vanna_1pct']:.2f}")
    cols2[5].metric("RHO / 1%", f"{cg['rho_1pct']:.2f}")

    # ── EXPANDERS ────────────────────────────────────────────
    # Gamma PnL Calculator
    with st.expander("Gamma PnL Calculator"):
        col_a, col_b = st.columns(2)
        spot_move = col_a.number_input("Spot move %", value=1.00, step=0.50, format="%.2f",
                                       key="gamma_spot_move")
        iv_new_pct = col_b.number_input("IV %", value=params["sigma_pct"], step=1.00, format="%.1f",
                                        key="gamma_iv")

        spot_move_dec = spot_move / 100
        new_S = S * (1 + spot_move_dec)
        new_delta_cash = delta(new_S, K, T, r, q, sigma, otype) * lots * mult * new_S
        gamma_pnl = 0.5 * gamma(S, K, T, r, q, sigma) * (S * spot_move_dec) ** 2 * lots * mult
        daily_move = sigma * np.sqrt(1 / 252) * 100

        cols3 = st.columns(4)
        cols3[0].metric("NEW Δ CASH", f"{new_delta_cash:.0f}")
        cols3[1].metric("GAMMA PNL", f"{gamma_pnl:.2f}")
        cols3[2].metric("DAILY MOVE", f"{daily_move:.2f}%")

    # Trading Shortcuts
    with st.expander("Trading Shortcuts"):
        gamma_val = gamma(S, K, T, r, q, sigma)
        theta_day_val = theta(S, K, T, r, q, sigma, otype) / 365

        # BE SPOT: break-even spot at expiry
        be_spot = K + price if otype == "call" else K - price
        be_pct = (be_spot / S - 1) * 100

        # BE VOL (REALIZED): break-even realized vol
        if gamma_val > 0 and theta_day_val < 0:
            be_vol = np.sqrt(2 * abs(theta_day_val) / (gamma_val * S**2) * 252) * 100
        else:
            be_vol = 0.0

        # GAMMA / THETA ratio
        gamma_theta = abs(cg['gamma_1pct'] / cg['theta_day']) if cg['theta_day'] != 0 else 0.0

        # THETA EARN MOVE: daily move to earn back theta
        if gamma_val > 0 and theta_day_val < 0:
            delta_s = np.sqrt(2 * abs(theta_day_val) / gamma_val)
            theta_earn_pct = (delta_s / S) * 100
        else:
            delta_s = 0.0
            theta_earn_pct = 0.0

        cols_ts = st.columns(4)
        cols_ts[0].metric("BE SPOT", f"{be_spot:.2f}", delta=f"{be_pct:+.2f}%")
        cols_ts[1].metric("BE VOL (REALIZED)", f"{be_vol:.2f}%")
        cols_ts[2].metric("GAMMA / THETA", f"{gamma_theta:.2f}")
        cols_ts[3].metric("THETA EARN MOVE", f"{theta_earn_pct:.2f}%")

        st.caption(f"[{S - delta_s:.2f}, {S + delta_s:.2f}] · {int(delta_s / 0.01)} ticks")

    # Quick Calc — Gamma → Theta Bill
    with st.expander("Quick Calc — Gamma → Theta Bill"):
        col_g, col_v = st.columns(2)
        gamma_notional = col_g.number_input("Gamma $ notional", value=20_000_000, step=1_000_000,
                                            format="%d", key="gamma_notional")
        vol_pct = col_v.number_input("Vol %", value=params["sigma_pct"], step=1.00, format="%.1f",
                                     key="theta_vol")

        theta_bill = gamma_notional * vol_pct**2 / 50_400
        daily_move_pct = vol_pct / np.sqrt(252)

        col_t, col_d = st.columns(2)
        col_t.metric("Θ / DAY", f"${theta_bill:,.0f}")
        col_d.metric("DAILY MOVE", f"{daily_move_pct:.2f}%")

        st.caption(f"= CΓ × σ² / 50,400")

    # # Early Exercise Analysis
    # with st.expander("Early Exercise Analysis — American Style"):
    #     intrinsic_call = max(S - K, 0)
    #     intrinsic_put = max(K - S, 0)
    #     euro_call = price
    #     euro_put = bs_price(S, K, T, r, q, sigma, "put")
    #     time_value_call = euro_call - intrinsic_call
    #     time_value_put = euro_put - intrinsic_put
    #     st.markdown(f"""...""") 

    # ── UNIT GREEKS TABLE ────────────────────────────────────
    st.markdown("#### UNIT GREEKS")
    ug = unit_greeks(S, K, T, r, q, sigma, otype)

    greeks_data = []
    for key in ug:
        greeks_data.append({
            "Greek": key,
            "Value": f"{ug[key]:.6f}",
        })
    st.dataframe(pd.DataFrame(greeks_data), width='stretch', hide_index=True)

    # ── VISUALIZATIONS ───────────────────────────────────────
    st.markdown("#### CHARTS")

    spots = np.linspace(S * 0.7, S * 1.3, 100)
    times = np.linspace(0.01, T, 100)
    sigmas_list = [0.10, 0.20, 0.40]
    if otype == "call":
        moneyness = {"OTM": K * 0.9, "ATM": K, "ITM": K * 1.1}
    else:
        moneyness = {"OTM": K * 1.1, "ATM": K, "ITM": K * 0.9}

    vols = np.linspace(0.05, 0.60, 100)

    # Price vs Spot | Price vs Vol | Price vs Maturity
    other_type = "put" if otype == "call" else "call"
    col1, col2, col3 = st.columns(3)
    with col1:
        fig = go.Figure()
        vals_c = [bs_price(s, K, T, r, q, sigma, "call") for s in spots]
        vals_p = [bs_price(s, K, T, r, q, sigma, "put") for s in spots]
        fig.add_trace(go.Scatter(x=spots, y=vals_c, mode="lines", name="Call",
                                 line=dict(width=2, color="#1f77b4")))
        fig.add_trace(go.Scatter(x=spots, y=vals_p, mode="lines", name="Put",
                                 line=dict(width=2, color="#d62728")))
        fig.add_vline(x=K, line=dict(color="#ccc", dash="dash", width=1),
                      annotation_text="ATM", annotation_position="top")
        fig.update_layout(title="Price vs Spot",
                          xaxis_title="Spot", yaxis_title="Price",
                          height=350, margin=dict(l=50, r=30, t=40, b=50),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
        st.plotly_chart(fig, width='stretch')

    with col2:
        fig = go.Figure()
        pv_c = [bs_price(S, K, T, r, q, v, "call") for v in vols]
        pv_p = [bs_price(S, K, T, r, q, v, "put") for v in vols]
        fig.add_trace(go.Scatter(x=vols * 100, y=pv_c, mode="lines", name="Call",
                                 line=dict(width=2, color="#1f77b4")))
        fig.add_trace(go.Scatter(x=vols * 100, y=pv_p, mode="lines", name="Put",
                                 line=dict(width=2, color="#d62728")))
        fig.update_layout(title="Price vs Vol",
                          xaxis_title="Volatility (%)", yaxis_title="Price",
                          height=350, margin=dict(l=50, r=30, t=40, b=50),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
        st.plotly_chart(fig, width='stretch')

    with col3:
        fig = go.Figure()
        times_long = np.linspace(0.01, T * 3, 100)
        pt_c = [bs_price(S, K, t, r, q, sigma, "call") for t in times_long]
        pt_p = [bs_price(S, K, t, r, q, sigma, "put") for t in times_long]
        fig.add_trace(go.Scatter(x=times_long, y=pt_c, mode="lines", name="Call",
                                 line=dict(width=2, color="#1f77b4")))
        fig.add_trace(go.Scatter(x=times_long, y=pt_p, mode="lines", name="Put",
                                 line=dict(width=2, color="#d62728")))
        fig.update_layout(title="Price vs Maturity",
                          xaxis_title="Time to Maturity (y)", yaxis_title="Price",
                          height=350, margin=dict(l=50, r=30, t=40, b=50),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
        st.plotly_chart(fig, width='stretch')

    # ── GREEKS ──────────────────────────────────────────────
    st.markdown("#### UNIT GREEKS SENSITIVITY")

    # Delta
    col1, col2 = st.columns(2)
    with col1:
        fig = greek_vs_spot_by_vol(spots, delta, S, K, T, r, q, sigmas_list,
                                    "Delta vs Spot — by Volatility", "Delta")
        st.plotly_chart(fig, width='stretch')
    with col2:
        fig = greek_vs_time_by_moneyness(times, delta, S, K, r, q, sigma, moneyness,
                                          "Delta vs Time — by Moneyness", "Delta")
        st.plotly_chart(fig, width='stretch')

    # Gamma
    col1, col2 = st.columns(2)
    with col1:
        fig = greek_vs_spot_by_vol(spots, gamma, S, K, T, r, q, sigmas_list,
                                    "Gamma vs Spot — by Volatility", "Gamma")
        st.plotly_chart(fig, width='stretch')
    with col2:
        fig = greek_vs_time_by_moneyness(times, gamma, S, K, r, q, sigma, moneyness,
                                          "Gamma vs Time — by Moneyness", "Gamma")
        st.plotly_chart(fig, width='stretch')

    # Vega
    col1, col2 = st.columns(2)
    with col1:
        fig = greek_vs_spot_by_vol(spots, vega, S, K, T, r, q, sigmas_list,
                                    "Vega vs Spot — by Volatility", "Vega")
        st.plotly_chart(fig, width='stretch')
    with col2:
        fig = greek_vs_time_by_moneyness(times, vega, S, K, r, q, sigma, moneyness,
                                          "Vega vs Time — by Moneyness", "Vega")
        st.plotly_chart(fig, width='stretch')

    # Theta
    col1, col2 = st.columns(2)
    with col1:
        fig = greek_vs_spot_by_vol(spots, theta, S, K, T, r, q, sigmas_list,
                                    "Theta vs Spot — by Volatility", "Theta")
        st.plotly_chart(fig, width='stretch')
    with col2:
        fig = greek_vs_time_by_moneyness(times, theta, S, K, r, q, sigma, moneyness,
                                          "Theta vs Time — by Moneyness", "Theta")
        st.plotly_chart(fig, width='stretch')

    # Rho
    col1, col2 = st.columns(2)
    with col1:
        fig = greek_vs_spot_by_vol(spots, rho, S, K, T, r, q, sigmas_list,
                                    "Rho vs Spot — by Volatility", "Rho")
        st.plotly_chart(fig, width='stretch')
    with col2:
        fig = greek_vs_time_by_moneyness(times, rho, S, K, r, q, sigma, moneyness,
                                          "Rho vs Time — by Moneyness", "Rho")
        st.plotly_chart(fig, width='stretch')

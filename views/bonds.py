"""
Bonds page — Fixed-income pricing, duration, convexity, and Q&A.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.bonds_math import (
    bond_price, duration_convexity, dv01, pv01,
    price_vs_yield_data, cashflow_pv_data,
    callable_bond_price, putable_bond_price, callable_putable_bond_price,
    yield_to_call, yield_to_put,
)


def render_sidebar():
    """Render Bonds sidebar and return parameters."""
    st.sidebar.markdown("#### Bond Parameters")

    face = st.sidebar.number_input("Face", value=1000.0, step=100.0, format="%.0f")
    coupon_pct = st.sidebar.number_input("Coupon %", value=5.00, step=0.25, format="%.2f")

    col_m, col_y = st.sidebar.columns(2)
    maturity = col_m.number_input("Mat. (y)", value=10.0, step=0.5, format="%.1f")
    ytm_pct = col_y.number_input("YTM %", value=5.00, step=0.25, format="%.2f")

    col_s, col_f = st.sidebar.columns(2)
    settl_days = col_s.number_input("Settl. d", value=0, step=1, min_value=0)
    freq = col_f.selectbox("Freq", options=[1, 2, 4], index=1)

    st.sidebar.markdown("---")
    st.sidebar.caption("Risk")

    notional = st.sidebar.number_input("Notional", value=1000000, step=100000, format="%d")
    shift_bp = st.sidebar.number_input("Shift (bp)", value=1.0, step=1.0, format="%.1f")

    st.sidebar.markdown("---")
    st.sidebar.caption("Embedded Options")

    callable_on = st.sidebar.checkbox("Callable", value=False)
    call_price_val = None
    call_date_years = None
    if callable_on:
        call_price_val = st.sidebar.number_input("Call Price", value=face, step=10.0, format="%.0f")
        call_date_years = st.sidebar.number_input("Call Date (y)", value=min(5.0, maturity), step=0.5, format="%.1f")

    putable_on = st.sidebar.checkbox("Putable", value=False)
    put_price_val = None
    put_date_years = None
    if putable_on:
        put_price_val = st.sidebar.number_input("Put Price", value=face, step=10.0, format="%.0f")
        put_date_years = st.sidebar.number_input("Put Date (y)", value=min(5.0, maturity), step=0.5, format="%.1f")

    rate_vol_pct = None
    if callable_on or putable_on:
        rate_vol_pct = st.sidebar.number_input("Rate vol %", value=20.0, step=1.0, format="%.1f")

    return {
        "face": face,
        "coupon_rate": coupon_pct / 100,
        "ytm": ytm_pct / 100,
        "maturity": maturity,
        "freq": freq,
        "settl_days": settl_days,
        "notional": notional,
        "shift_bp": shift_bp,
        "callable_on": callable_on,
        "call_price": call_price_val,
        "call_date_years": call_date_years,
        "putable_on": putable_on,
        "put_price": put_price_val,
        "put_date_years": put_date_years,
        "rate_vol_pct": rate_vol_pct,
    }


def render(params):
    """Render the Bonds main content area."""
    face = params["face"]
    coupon_rate = params["coupon_rate"]
    ytm = params["ytm"]
    maturity = params["maturity"]
    freq = params["freq"]
    settl_days = params["settl_days"]
    notional = params["notional"]
    shift_bp = params["shift_bp"]

    # ── PRICING ──────────────────────────────────────────────
    st.markdown("#### BOND PRICING")
    st.markdown("---")

    bp = bond_price(face, coupon_rate, ytm, maturity, freq, settl_days)
    dc = duration_convexity(face, coupon_rate, ytm, maturity, freq, settl_days)
    _dv01 = dv01(face, coupon_rate, ytm, maturity, freq, settl_days)
    _pv01 = pv01(face, coupon_rate, ytm, maturity, freq, settl_days, notional, shift_bp)
    pv01_notional = _dv01 / face * notional

    cols = st.columns(3)
    cols[0].metric("DIRTY PRICE", f"{bp['dirty_price']:.2f}")
    cols[1].metric("CLEAN PRICE", f"{bp['clean_price']:.2f}")
    cols[2].metric("ACCRUED INTEREST", f"{bp['accrued_interest']:.4f}")

    st.markdown("#### DURATION & CONVEXITY")
    st.markdown("---")
    cols2 = st.columns(3)
    cols2[0].metric("MACAULAY DURATION", f"{dc['mac_duration']:.4f} y")
    cols2[1].metric("MODIFIED DURATION", f"{dc['mod_duration']:.4f} y")
    cols2[2].metric("CONVEXITY", f"{dc['convexity']:.4f}")

    st.markdown("#### RISK SENSITIVITY")
    st.markdown("---")
    cols3 = st.columns(3)
    cols3[0].metric("DV01 (PER BOND)", f"{_dv01:.4f}")
    cols3[1].metric("PV01 (NOTIONAL)", f"{pv01_notional:,.2f}")
    cols3[2].metric("PNL (+1 BP)", f"{_pv01:,.2f}")

    if params.get("callable_on") or params.get("putable_on"):
        rate_vol = (params.get("rate_vol_pct") or 0.0) / 100
        
        title = "CALLABLE BOND ANALYSIS"
        if params.get("putable_on") and not params.get("callable_on"):
            title = "PUTABLE BOND ANALYSIS"
        elif params.get("callable_on") and params.get("putable_on"):
            title = "CALLABLE & PUTABLE BOND ANALYSIS"
            
        st.markdown(f"#### {title}")
        st.markdown("---")
        
        cols4 = st.columns(4)
        
        if params.get("callable_on") and not params.get("putable_on"):
            res = callable_bond_price(face, coupon_rate, ytm, maturity, freq, settl_days,
                                       params["call_price"], params["call_date_years"], rate_vol)
            op_price = res["callable_price"]
            tree_straight = res["straight_price"]
            yt_ex = yield_to_call(face, coupon_rate, bp["dirty_price"], settl_days, freq, params["call_price"], params["call_date_years"])
            cols4[0].metric("CALLABLE PRICE", f"{op_price:.4f}")
            
        elif params.get("putable_on") and not params.get("callable_on"):
            res = putable_bond_price(face, coupon_rate, ytm, maturity, freq, settl_days,
                                      params["put_price"], params["put_date_years"], rate_vol)
            op_price = res["putable_price"]
            tree_straight = res["straight_price"]
            yt_ex = yield_to_put(face, coupon_rate, bp["dirty_price"], settl_days, freq, params["put_price"], params["put_date_years"])
            cols4[0].metric("PUTABLE PRICE", f"{op_price:.4f}")
            
        elif params.get("callable_on") and params.get("putable_on"):
            res = callable_putable_bond_price(face, coupon_rate, ytm, maturity, freq, settl_days,
                                                params["call_price"], params["call_date_years"],
                                                params["put_price"], params["put_date_years"], rate_vol)
            op_price = res["price"]
            tree_straight = res["straight_price"]
            yt_ex = yield_to_call(face, coupon_rate, bp["dirty_price"], settl_days, freq, params["call_price"], params["call_date_years"])
            cols4[0].metric("CALL & PUT PRICE", f"{op_price:.4f}")

        option_value = abs(tree_straight - op_price)
        cols4[1].metric("OPTION VALUE", f"{option_value:.4f}")
        
        ytw = min(ytm, yt_ex) if params.get("callable_on") else max(ytm, yt_ex)
        if params.get("callable_on") and not params.get("putable_on"):
            cols4[2].metric("YIELD TO CALL", f"{yt_ex*100:.4f}%")
            cols4[3].metric("YIELD TO WORST", f"{ytw*100:.4f}%")
        elif params.get("putable_on") and not params.get("callable_on"):
            cols4[2].metric("YIELD TO PUT", f"{yt_ex*100:.4f}%")
            cols4[3].metric("YIELD TO WORST", f"{ytw*100:.4f}%")

    # ── CHARTS ───────────────────────────────────────────────
    st.markdown("#### CHARTS")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Bond Price vs Yield**")
        callable_on = params.get("callable_on", False)
        putable_on = params.get("putable_on", False)
        
        if callable_on or putable_on:
            ytms, prices, call_prices, put_prices = price_vs_yield_data(
                face, coupon_rate, maturity, freq, settl_days,
                callable_on=callable_on, call_price=params.get("call_price"), 
                call_date_years=params.get("call_date_years"), 
                putable_on=putable_on, put_price=params.get("put_price"),
                put_date_years=params.get("put_date_years"),
                rate_vol=rate_vol
            )
        else:
            ytms, prices = price_vs_yield_data(face, coupon_rate, maturity, freq, settl_days)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ytms * 100, y=prices, mode="lines",
                                  name="Straight", line=dict(color="#1f77b4", width=2)))
        
        if callable_on:
            fig.add_trace(go.Scatter(x=ytms * 100, y=call_prices, mode="lines",
                                      name="Callable", line=dict(color="#d62728", width=2)))
                                      
        if putable_on:
            fig.add_trace(go.Scatter(x=ytms * 100, y=put_prices, mode="lines",
                                      name="Putable", line=dict(color="#2ca02c", width=2)))
                                      
        fig.add_hline(y=face, line=dict(color="#999", dash="dash", width=1),
                      annotation_text="Par", annotation_position="right")
        fig.update_layout(
            xaxis_title="YTM (%)", yaxis_title="Price",
            height=400, margin=dict(l=50, r=30, t=20, b=50),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.markdown("**Present Value of Cash Flows**")
        periods, cpn_pvs, prin_pvs = cashflow_pv_data(face, coupon_rate, ytm, maturity, freq, settl_days)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=periods, y=cpn_pvs, name="Coupon PV",
                              marker_color="#1f77b4"))
        fig.add_trace(go.Bar(x=periods, y=prin_pvs, name="Principal PV",
                              marker_color="#d62728"))
        fig.update_layout(
            barmode="stack",
            xaxis_title="Maturity (y)", yaxis_title="PV",
            height=400, margin=dict(l=50, r=30, t=20, b=50),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig, width='stretch')



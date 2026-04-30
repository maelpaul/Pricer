"""
Reusable Plotly chart builders for the Skema Pricer.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


# Consistent color palette
COLORS = {
    "blue": "#1f77b4",
    "red": "#d62728",
    "green": "#2ca02c",
    "purple": "#9467bd",
    "orange": "#ff7f0e",
    "gray": "#7f7f7f",
    "light_gray": "#c7c7c7",
}

SIGMA_COLORS = {
    10: "#00bcd4",   # cyan
    20: "#1f77b4",   # dark blue
    40: "#d62728",   # red
}

MONEYNESS_COLORS = {
    "OTM": "#d62728",   # red
    "ATM": "#1f77b4",   # blue
    "ITM": "#2ca02c",   # green
}


def _base_layout(title=None, xaxis_title=None, yaxis_title=None, height=350):
    """Base layout for consistent styling."""
    return dict(
        title=dict(text=title, font=dict(size=14)) if title else None,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        margin=dict(l=50, r=30, t=40 if title else 20, b=50),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        xaxis=dict(gridcolor="#eee", zerolinecolor="#ccc"),
        yaxis=dict(gridcolor="#eee", zerolinecolor="#ccc"),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5,
                    font=dict(size=10)),
    )


def greek_vs_spot_by_vol(spots, greek_fn, S, K, T, r, q, sigmas=[0.10, 0.20, 0.40],
                         title="", yaxis_title="", option_type="call"):
    """Plot a Greek vs Spot for multiple volatility levels."""
    fig = go.Figure()
    for sig in sigmas:
        vals = [greek_fn(s, K, T, r, q, sig, option_type) if 'option_type' in greek_fn.__code__.co_varnames
                else greek_fn(s, K, T, r, q, sig) for s in spots]
        fig.add_trace(go.Scatter(
            x=spots, y=vals, mode="lines",
            name=f"σ = {int(sig * 100)}%",
            line=dict(color=SIGMA_COLORS.get(int(sig * 100), "#333"), width=2),
        ))
    # ATM vertical line
    fig.add_vline(x=K, line=dict(color="#ccc", dash="dash", width=1),
                  annotation_text="ATM", annotation_position="top")
    fig.update_layout(**_base_layout(title, "Spot", yaxis_title))
    return fig


def greek_vs_time_by_moneyness(times, greek_fn, S, K, r, q, sigma,
                                moneyness_spots=None, title="", yaxis_title="",
                                option_type="call"):
    """Plot a Greek vs Time for different moneyness levels."""
    if moneyness_spots is None:
        moneyness_spots = {"OTM": K * 0.9, "ATM": K, "ITM": K * 1.1}
    labels = {
        "OTM": f"OTM (S={moneyness_spots['OTM']:.0f})",
        "ATM": f"ATM (S={moneyness_spots['ATM']:.0f})",
        "ITM": f"ITM (S={moneyness_spots['ITM']:.0f})",
    }
    fig = go.Figure()
    for key, spot in moneyness_spots.items():
        vals = []
        for t in times:
            try:
                if 'option_type' in greek_fn.__code__.co_varnames:
                    vals.append(greek_fn(spot, K, t, r, q, sigma, option_type))
                else:
                    vals.append(greek_fn(spot, K, t, r, q, sigma))
            except Exception:
                vals.append(0.0)
        fig.add_trace(go.Scatter(
            x=times, y=vals, mode="lines",
            name=labels[key],
            line=dict(color=MONEYNESS_COLORS[key], width=2),
        ))
    fig.update_layout(**_base_layout(title, "Time to Maturity (y)", yaxis_title))
    return fig


def price_vs_spot(spots, S, K, T, r, q, sigmas, bs_price_fn, title="Price vs Spot"):
    """Price vs Spot for Call and Put at multiple volatilities."""
    fig = go.Figure()
    for sig in sigmas:
        call_prices = [bs_price_fn(s, K, T, r, q, sig, "call") for s in spots]
        put_prices = [bs_price_fn(s, K, T, r, q, sig, "put") for s in spots]
        fig.add_trace(go.Scatter(
            x=spots, y=call_prices, mode="lines",
            name=f"Call σ={int(sig*100)}%",
            line=dict(color=SIGMA_COLORS.get(int(sig*100), "#333"), width=2),
        ))
    fig.add_vline(x=K, line=dict(color="#ccc", dash="dash", width=1))
    fig.update_layout(**_base_layout(title, "Spot", "Price"))
    return fig


def dual_axis_chart(x, y1, y2, name1, name2, x_title, y1_title, y2_title, title="",
                    color1=COLORS["blue"], color2=COLORS["red"]):
    """Chart with two y-axes."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=x, y=y1, name=name1,
                             line=dict(color=color1, width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=y2, name=name2,
                             line=dict(color=color2, width=2, dash="dot")),
                  secondary_y=True)
    layout = _base_layout(title, x_title, y1_title)
    fig.update_layout(**layout)
    fig.update_yaxes(title_text=y1_title, secondary_y=False)
    fig.update_yaxes(title_text=y2_title, secondary_y=True)
    return fig


def payoff_chart(S_range, payoff_cert, payoff_stock=None, entry_price=None,
                 title="Payoff at Maturity", cert_name="Certificate",
                 annotations=None, barrier=None, cap=None, spot=None):
    """Generic payoff chart for structured products."""
    fig = go.Figure()

    if payoff_stock is not None:
        fig.add_trace(go.Scatter(
            x=S_range, y=payoff_stock, mode="lines",
            name="Stock", line=dict(color=COLORS["gray"], width=1.5, dash="dash"),
        ))

    fig.add_trace(go.Scatter(
        x=S_range, y=payoff_cert, mode="lines",
        name=cert_name, line=dict(color=COLORS["blue"] if entry_price is None else COLORS["red"], width=2.5),
    ))

    # Barrier line
    if barrier is not None:
        fig.add_vline(x=barrier, line=dict(color="#999", dash="dashdot", width=1),
                      annotation_text="B", annotation_position="bottom")

    # Spot line
    if spot is not None:
        fig.add_vline(x=spot, line=dict(color="#ccc", dash="dash", width=1),
                      annotation_text="S₀", annotation_position="bottom")

    # Cap line
    if cap is not None:
        fig.add_hline(y=cap, line=dict(color=COLORS["red"], dash="dot", width=1),
                      annotation_text=f"Cap ({cap:.1f})", annotation_position="right")

    if annotations:
        for ann in annotations:
            fig.add_annotation(**ann)

    fig.update_layout(**_base_layout(title, "Underlying at Expiry" if entry_price is None else "Underlying at Expiry", ""))
    return fig

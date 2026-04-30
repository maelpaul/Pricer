# Options and Bonds Pricer

An interactive derivatives pricing application built with **Streamlit**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57+-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

**🚀 Live App:** [options-and-bonds-pricer.streamlit.app](https://options-and-bonds-pricer.streamlit.app/)

---

## Features

### 📊 Options (Black-Scholes)
- European call & put pricing with full Greeks suite
- **Cash Greeks**: Delta, Gamma/1%, Theta/day, Vega/1%, Charm/day, Vanna/1%, Rho/1%
- **Interactive tools**: Gamma PnL Calculator, Trading Shortcuts, Quick Calc (Gamma → Theta Bill), Early Exercise Analysis
- **10 sensitivity charts**: Price, Delta, Gamma, Vega, Theta — each plotted vs Spot (by volatility) and vs Time (by moneyness)
- Unit Greeks table with Call & Put comparison

### 🏦 Bonds
- Clean & dirty price, accrued interest
- Duration (Macaulay & Modified), Convexity
- DV01, PV01 with configurable notional and shift
- Bond Price vs Yield curve, PV of Cash Flows bar chart
- Callable bond support
- **Interview Q&A** section with 7 bonds/swaps questions

### 🚀 Coming Soon (In Development)
- **Turbo (Open-End Knock-Out)**: Pricing, distance to barrier, daily funding cost.
- **Discount Certificate**: Replication strategies, discount %, sideways return.
- **Bonus Certificate**: Down-and-out put barrier option pricing.
- **Interview Q&A**: 30+ finance interview questions with detailed answers.

---

## Quick Start

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/maelpaul/Pricer.git
cd Pricer

# Create venv and install all dependencies (one command)
uv sync

# Run the application
uv run streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## Project Structure

```
Pricer/
├── app.py                        # Main Streamlit entrypoint (routing & CSS)
├── pyproject.toml                # Project config & dependencies (uv)
├── uv.lock                      # Dependency lockfile
├── .venv/                       # Virtual environment (created by uv)
│
├── core/                        # Math engines
│   ├── black_scholes.py         # Black-Scholes pricing + 10 Greeks
│   └── bonds_math.py            # Bond pricing, duration, convexity, DV01
│   # ├── turbo_math.py            # (WIP) Turbo certificate pricing
│   # ├── discount_cert_math.py    # (WIP) Discount certificate replication
│   # └── bonus_cert_math.py       # (WIP) Bonus certificate
├── utils/                       # Utilities
│   ├── formatting.py            # Number formatting helpers
│   └── charts.py                # Reusable Plotly chart builders
│
└── views/                       # Page modules
    ├── options.py               # Options page
    └── bonds.py                 # Bonds page
    # ├── turbo.py                 # (WIP) Turbo page
    # ├── discount_cert.py         # (WIP) Discount Certificate page
    # ├── bonus_cert.py            # (WIP) Bonus Certificate page
    # └── interview.py             # (WIP) Interview Q&A page
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web application framework |
| `numpy` | Numerical computing |
| `scipy` | Statistical functions (normal CDF/PDF) |
| `plotly` | Interactive charts |
| `pandas` | DataFrames for tables |

All dependencies are managed via `uv` and pinned in `uv.lock`.

---

## Usage

### Development

```bash
# Run with auto-reload
uv run streamlit run app.py

# Add a new dependency
uv add <package>

# Update all dependencies
uv lock --upgrade
uv sync
```

### Deployment (Railway / Streamlit Cloud)

The app can be deployed to any platform that supports Python:

```bash
# Railway: set the start command to
uv run streamlit run app.py --server.port $PORT --server.headless true
```

---

## Mathematical Models

### Black-Scholes
$$C = S e^{-qT} N(d_1) - K e^{-rT} N(d_2)$$

### Greeks Implemented
Delta, Gamma, Theta, Vega, Rho, Charm, Vanna, Volga, Speed, Color

### Barrier Options (Bonus Certificate)
*Coming Soon*

### Bond Pricing
$$P = \sum_{i=1}^{n} \frac{C}{(1+y/f)^i} + \frac{FV}{(1+y/f)^n}$$

---

## Author

Created by [Maël PAUL](https://github.com/maelpaul).

---

## License

MIT

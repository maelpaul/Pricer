"""
Number formatting helpers.
"""


def fmt(value, decimals=2):
    """Format number with specified decimals."""
    if value is None:
        return "N/A"
    try:
        return f"{value:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def fmt_pct(value, decimals=2):
    """Format as percentage string."""
    if value is None:
        return "N/A"
    try:
        return f"{value:.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


def fmt_int(value):
    """Format as integer with thousands separator."""
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)

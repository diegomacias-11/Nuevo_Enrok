from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    try:
        return Decimal(value) * Decimal(arg)
    except Exception:
        return ""

@register.filter
def pct(value, decimals=0):
    """Render a Decimal fraction (0..1) as percent without scientific notation.

    Usage in templates: {{ value|pct }} or {{ value|pct:2 }} for 2 decimals.
    """
    try:
        d = Decimal(value) * Decimal(100)
        decs = int(decimals)
        s = f"{d:.{decs}f}"
        if decs == 0:
            s = s.split(".")[0]
        return f"{s}%"
    except Exception:
        return ""

@register.filter
def currency(value, decimals=2):
    """Format a number as currency with thousands separators and $.

    Usage: {{ value|currency }} or {{ value|currency:0 }}
    """
    try:
        d = Decimal(str(value))
    except Exception:
        return ""
    try:
        decs = int(decimals)
    except Exception:
        decs = 2
    fmt = f"{{:,.{decs}f}}"
    return f"${fmt.format(d)}"

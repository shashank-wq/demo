"""Moisture classification and alert rules.

Thresholds are typical for paddy storage (about 12-14% moisture is safe).
Confirm the exact values with your faculty guide / a domain source.
"""

DRY_BELOW = 12.0
EXCESS_ABOVE = 14.0
HUMIDITY_WARN = 75.0
TEMP_WARN = 35.0


def classify(moisture: float) -> str:
    if moisture < DRY_BELOW:
        return "dry"
    if moisture > EXCESS_ABOVE:
        return "excess"
    return "optimal"


def build_alerts(moisture: float, temperature: float, humidity: float):
    """Return a list of (severity, message) tuples."""
    alerts = []
    if moisture > EXCESS_ABOVE + 2:
        alerts.append(("critical", f"Moisture {moisture:.1f}% is very high - spoilage risk. Dry the grain now."))
    elif moisture > EXCESS_ABOVE:
        alerts.append(("warning", f"Moisture {moisture:.1f}% is above {EXCESS_ABOVE}%. Dry the grain."))
    elif moisture < DRY_BELOW:
        alerts.append(("warning", f"Moisture {moisture:.1f}% is below {DRY_BELOW}%. Grain is over-dried, weight loss and breakage likely."))
    if humidity > HUMIDITY_WARN:
        alerts.append(("warning", f"Humidity {humidity:.0f}% is high. Improve ventilation in storage."))
    if temperature > TEMP_WARN:
        alerts.append(("warning", f"Temperature {temperature:.1f} C is high for storage."))
    return alerts

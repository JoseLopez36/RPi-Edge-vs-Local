"""
Sensor helpers for telemetry (temperature, etc.).
"""

from pathlib import Path


def get_cpu_temp_c():
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        raw = thermal_path.read_text().strip()
        return float(raw) / 1000.0
    except Exception:
        return None
from datetime import datetime, timezone
from typing import Literal

from datetime_util import to_local

# define type for tariff names
FluxTariffName = Literal["DAY", "FLUX", "PEAK"]

meg_tariff = 0.15  # Minimum Export Guarantee Tariff (£)

# Import prices in pence per kWh
import_prices = {
    "DAY": 27.33,
    "FLUX": 16.4,
    "PEAK": 38.26,
}

# Export rates in pence per kWh
export_rates = {
    "DAY": 10.11,
    "FLUX": 4.99,
    "PEAK": 29.32,
}


def tariff_name_from_time(interval_start: datetime) -> FluxTariffName:
    # tariff is based on localtime, not UTC
    if interval_start.tzinfo is not None:
        raise ValueError("expecting naive datetime to be interpreted as UTC")
    interval_start = to_local(interval_start.replace(tzinfo=timezone.utc))
    if interval_start.hour >= 2 and interval_start.hour < 5:
        return "FLUX"
    if interval_start.hour >= 16 and interval_start.hour < 19:
        return "PEAK"
    return "DAY"

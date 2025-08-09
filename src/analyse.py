import logging
import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB
from datetime_util import to_utc
from octopus_tariff import export_rates, meg_tariff, tariff_name_from_time

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to analyze electricity data and generate reports."""
    analyze_electricity_export()


def analyze_electricity_export() -> None:
    # Process in reverse order, starting from the most recent record.
    log.info("Starting export analysis.")
    results = group_by_day_and_tariff(DB.Export)

    # log the results usage per day per tariff
    for day, usage in results.items():
        log.info(
            f"On {day} exports per rate were { {k: f'{v:.3f}kWh' for k, v in usage.items()} }"
        )

    # print the results revenue breakdown per day per tariff in csv format
    print("date,peak,day,flux,total_revenue,meg_comparison")
    for day, data in results.items():
        row = [day]
        total_revenue = 0
        for tariff in ["PEAK", "DAY", "FLUX"]:
            rate = export_rates[tariff]
            energy = data.get(tariff, 0)
            revenue = energy * rate / 100  # Convert pence to pounds
            row.append(f"£{revenue:.2f}")
            total_revenue += revenue
        row.append(f"£{total_revenue:.2f}")
        total_energy = sum(data.values())
        # Calculate comparative revenue if min export guarantee tariff was chosen
        megc = total_energy * meg_tariff
        row.append(f"£{megc:.2f}")
        print(",".join(row))


def group_by_day_and_tariff(table_class: DB.Import | DB.Export) -> dict[str, dict]:
    # Define the start date for analysis
    FROM_DT = to_utc(datetime.fromisoformat("2025-07-01T23:00+00:00"))
    log.info("Extracting data from date: %s", FROM_DT.isoformat())

    results = defaultdict(dict)
    # Get selected records and group by day and tariff
    for r in DB.get_meter_data(table_class, FROM_DT):
        # Day key is in the form YYYY-MM-DD
        day_key = r.interval_start.strftime("%Y-%m-%d")

        # Accumulate energy_kwh against each tariff (kWh)
        tariff_name = tariff_name_from_time(r.interval_start)
        day_result = results[day_key]
        day_result[tariff_name] = day_result.get(tariff_name, 0) + r.energy_kwh
    return results


if __name__ == "__main__":
    main()

import logging
import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB
from datetime_util import to_utc
from octopus_tariff import get_flux_import_tariff, import_prices

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to analyze electricity data and generate reports."""
    analyze_electricity_data(DB.Import)


def analyze_electricity_data(table_class: DB.Import | DB.Export) -> None:
    # Process in reverse order, starting from the most recent record.
    # Define the start date for analysis
    FROM_DT = to_utc(datetime.fromisoformat("2025-08-05T23:00+00:00"))
    log.info("Starting analysis from date: %s", FROM_DT.isoformat())

    log.info("Starting data analysis.")
    results: dict[str, dict] = defaultdict(dict)

    # TODO refactor this block to a function
    # Get selected records and group by day and tariff
    for r in DB.get_all_in_reverse_order(table_class, FROM_DT):
        log.debug(
            "Processing record with interval_start: %sZ and energy_kwh %s",
            r.interval_start.isoformat(),
            r.energy_kwh,
        )

        # get the YYYY-MM-DD timestamp
        day_stamp = r.interval_start.strftime("%Y-%m-%d")
        log.debug("Processing data for day: %s", day_stamp)

        # Accumulate energy_kwh against each tariff in Wh integer
        tariff_name = get_flux_import_tariff(r.interval_start)
        day_result = results[day_stamp]
        day_result[tariff_name] = day_result.get(tariff_name, 0) + int(
            r.energy_kwh * 1000
        )

    log.info("Data analysis completed.")

    # log the results usage per day per tariff
    for day, usage in results.items():
        log.info("Day: %s usage (Wh) %s", day, usage)

    # print the results cost breakdown per day per tariff
    for day, cost in results.items():
        print(day, end="")
        for tariff, usage in cost.items():
            price = import_prices[tariff]
            cost = usage * price / 100000  # convert Wh to kWh and in £ not pence
            print(f" {tariff} {usage}Wh £{cost:.2f}", end="")
        print()


if __name__ == "__main__":
    main()

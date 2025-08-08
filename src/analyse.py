import logging
import os
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB
from datetime_util import to_utc

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARN").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to analyze electricity data and generate reports.
    We process in reverse order, starting from the most recent record."""
    # Define the start and stop date for analysis (inclusive)
    # fetch start date. Controls last value in output as displayed reverse order
    FROM_DT = to_utc(datetime.fromisoformat("2025-08-06T04:00+01:00"))
    # process stop point (note process in reverse order)
    TO_DT = None  # to_utc(datetime.fromisoformat("2025-08-06T03:00:00+01:00"))

    log.info("Starting data analysis")
    for r in DB.get_all_in_reverse_order(FROM_DT):
        if TO_DT and r.interval_start < TO_DT:
            break
        log.info(
            "Processing record with interval_start: %sZ", r.interval_start.isoformat()
        )

        # get the day of the year
        day_of_year = r.interval_start.timetuple().tm_yday
        print(day_of_year, r.interval_start.isoformat())

        # break
    log.info("Data analysis completed.")


if __name__ == "__main__":
    main()

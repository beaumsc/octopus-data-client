import logging
import os
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARN").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to analyze electricity data and generate reports.
    We process in reverse order, starting from the most recent record."""
    # Define the start date for analysis (UTC)
    FROM_DT = datetime.fromisoformat("2025-08-05T00:00").replace(tzinfo=DB.local_tz)
    TO_DT = datetime.fromisoformat("2025-08-04T23:30").replace(
        tzinfo=DB.local_tz
    )  # reverse order stop point!

    log.info("Starting data analysis")
    for r in DB.get_all_in_reverse_order(FROM_DT):
        if r.interval_start < TO_DT:
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

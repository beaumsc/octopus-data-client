import logging
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to analyze electricity data and generate reports.
    We process in reverse order, starting from the most recent record."""
    # Define the start date for analysis (UTC)
    FROM_DT = datetime.fromisoformat("2025-08-05T00:00")
    TO_DT = datetime.fromisoformat("2025-08-04T23:30")  # reverse order stop point!

    log.info("Starting data analysis")
    for r in DB.get_all_in_reverse_order(FROM_DT):
        if r.interval_start < TO_DT:
            break
        log.info(
            "Processing record with interval_start: %sZ", r.interval_start.isoformat()
        )
    log.info("Data analysis completed.")


if __name__ == "__main__":
    main()

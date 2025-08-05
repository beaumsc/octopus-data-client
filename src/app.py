import logging
import os
from datetime import datetime

from dotenv import load_dotenv

import db_client as DB
from octopus_api import get_electricity_consumption

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
load_dotenv()


def main() -> None:
    """Main function to fetch electricity data and store it in the database."""

    data_collection_start_date = os.environ.get("data_collection_start_date")
    if data_collection_start_date is None:
        raise ValueError(
            "Environment variable 'data_collection_start_date' is not set."
        )

    log.info("Starting data collection")
    db_youngest = DB.get_most_recent_entry_date()
    if db_youngest is not None:
        log.info(f"Most recent entry in DB: {db_youngest}")
    else:
        log.info("No previous data found, using collection start date.")
        # If no previous data, use the start date from the environment variable
        db_youngest = DB.localize(datetime.fromisoformat(data_collection_start_date))

    data = get_electricity_consumption(db_youngest)
    if not data:
        log.info(f"No new API data since {db_youngest}")
        raise SystemExit

    log.info(f"Got from API. From {data[-1].interval_end} to {data[0].interval_end}")
    log.info("Adding records to DB")
    for r in data:
        entry = DB.Elect(
            interval_end=r.interval_end,
            consumption=r.consumption,
        )
        DB.session.add(entry)
    DB.session.commit()


if __name__ == "__main__":
    main()

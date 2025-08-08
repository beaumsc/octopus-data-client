import logging
import os
from datetime import datetime, timedelta

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
    last = DB.interval_start_from_most_recent_record(DB.Import)
    if last is None:
        # If no previous data, use the start date from the environment variable
        start = datetime.fromisoformat(data_collection_start_date).astimezone(
            DB.local_tz
        )
        log.info(
            "No previous data found, using collection start date: %s",
            start.isoformat(),
        )
    else:
        log.info("Previous data found up to interval_start: %s", last.isoformat())
        # add 30 minutes to the start time to avoid duplicates
        start = last + timedelta(minutes=30)

    log.info("Fetching data from API starting from: %s", start.isoformat())
    data = get_electricity_consumption(period_from=start)
    if not data:
        raise SystemExit

    first, last = data[-1].interval_start, data[0].interval_start
    log.info("Got from API. From %s to %s", first.isoformat(), last.isoformat())

    DB.add_to_db(data)


if __name__ == "__main__":
    main()

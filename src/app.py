from datetime import datetime, timezone

import db_client as DB
from dotenv import load_dotenv

load_dotenv()
import logging

from octopus_api import get_electricity_consumption

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


def main() -> None:
    dt = datetime.fromisoformat("2024-04-24 01:00:00+01:00")
    print(repr(dt))
    dt_utc = dt.astimezone(timezone.utc)
    print(repr(dt_utc))

    db_youngest = DB.get_most_recent_entry_date()

    if db_youngest is None:
        db_youngest = datetime.fromisoformat("2024-04-17 21:30:00+01:00")

    print(repr(db_youngest))
    # return
    data = get_electricity_consumption(db_youngest)
    if not data:
        log.info(f"No new API data since {db_youngest.isoformat()}")
        raise SystemExit

    log.info(f"Got from API. From {data[0].interval_end} to {data[-1].interval_end}")
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

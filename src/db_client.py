import atexit
import logging
from datetime import datetime, timezone

import pytz
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

log = logging.getLogger()

Base = declarative_base()

local_tz = pytz.timezone("Europe/London")


class Elect(Base):
    """Electricity table. Timestamp is end of 30 minute period."""

    __tablename__ = "electricity"

    # sqlite3 does not natively support timezone, so we leave datetime as string
    interval_end = sa.Column(sa.DateTime, primary_key=True)
    consumption = sa.Column(sa.Float(precision=2))

    def __init__(self, *args, interval_end: datetime, **kwargs):
        interval_end = interval_end.astimezone(tz=timezone.utc)
        super().__init__(*args, interval_end=interval_end, **kwargs)


engine = sa.create_engine("sqlite:///data/energy.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def get_most_recent_entry_date() -> datetime | None:
    """If recent value exists, it is returned with local timezone info."""
    try:
        result = (
            session.query(Elect.interval_end)
            .order_by(sa.desc(Elect.interval_end))
            .limit(1)
            .one()
        )
        if result:
            return localize(result[0])
    except sa.exc.NoResultFound:
        pass


def localize(dt: datetime) -> datetime:
    """Convert a naive datetime to local timezone."""
    if dt.tzinfo is None:
        return local_tz.localize(dt)
    return dt.astimezone(local_tz)


def add_to_db(data: list) -> None:
    """Add all records to the database."""
    for r in data:
        entry = Elect(
            interval_end=r.interval_end,
            consumption=r.consumption,
        )
        session.add(entry)
    try:
        session.commit()
    except sa.exc.IntegrityError:
        log.warning("Duplicate entry detected, rolling back the transaction.")
        session.rollback()
    else:
        log.info(f"Added {len(data)} records to the database.")


def cleanup():
    session.close()


atexit.register(cleanup)

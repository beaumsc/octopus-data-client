import atexit
import logging
from datetime import datetime, timezone
from typing import Generator

import pytz
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

log = logging.getLogger()

Base = declarative_base()

local_tz = pytz.timezone("Europe/London")


class Import(Base):
    __tablename__ = "e_import"

    # don't store interval_end, it is not necessary
    interval_start = sa.Column(sa.DateTime, primary_key=True)
    consumption = sa.Column(sa.Float(precision=2))

    # sqlite3 stores datetime as string. It converts to datetime on IO. It does not
    # support timezone-aware datetimes, so we store and retrieve them as UTC
    def __init__(self, *args, interval_start: datetime, **kwargs):
        interval_start = interval_start.astimezone(tz=timezone.utc)
        super().__init__(*args, interval_start=interval_start, **kwargs)


# class Export(Base):
#     __tablename__ = "e_import"


engine = sa.create_engine("sqlite:///data/energy.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def interval_start_from_most_recent_record(table_class: Import) -> datetime | None:
    """If a most recent record is found, return it's period_end"""
    try:
        result = (
            session.query(table_class.interval_start)
            .order_by(sa.desc(table_class.interval_start))
            .limit(1)
            .one()
        )
        return result[0]
    except sa.exc.NoResultFound:
        pass


def get_all_in_reverse_order(from_dt: datetime) -> Generator[Import]:
    """Get records that exist after date given (older/more recent) and return in reverse
    order (eldest first)."""
    try:
        results = (
            session.query(Import.interval_start)
            .filter(Import.interval_start >= from_dt)
            .order_by(sa.desc(Import.interval_start))
            .all()
        )
    except sa.exc.NoResultFound:
        log.warning("No records found in the database.")
        return
    for r in results:
        yield r


def add_to_db(data: list) -> None:
    """Add all records to the database."""
    log.info("Adding records to DB")
    for r in data:
        entry = Import(
            interval_start=r.interval_start,
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


def localize(dt: datetime) -> datetime:
    """Convert a naive datetime to local timezone."""
    if dt.tzinfo is None:
        return local_tz.localize(dt)
    return dt.astimezone(local_tz)


def cleanup():
    session.close()


atexit.register(cleanup)

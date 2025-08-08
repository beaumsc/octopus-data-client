import atexit
import logging
from datetime import datetime, timezone
from typing import Generator

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

from datetime_util import local_tz

log = logging.getLogger()

Base = declarative_base()


class LocalToUTC(sa.types.TypeDecorator):
    """Converts datetimes to UTC for storage if naive or local. Retrieves as UTC"""

    impl = sa.DateTime

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # Convert to UTC and drop tzinfo for storage
        if value.tzinfo is None:
            value = local_tz.localize(value)
        value_utc = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value_utc

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # Assume DB value is UTC naive, convert to local
        value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(local_tz)


class Import(Base):
    __tablename__ = "e_import"

    # don't store interval_end, it is not necessary
    interval_start = sa.Column(LocalToUTC, primary_key=True)
    consumption = sa.Column(sa.Float(precision=2))


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


def cleanup():
    session.close()


atexit.register(cleanup)

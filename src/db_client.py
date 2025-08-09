import atexit
import logging
from datetime import datetime
from typing import Generator

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

from datetime_util import to_utc_naive

log = logging.getLogger()

Base = declarative_base()


class Import(Base):
    __tablename__ = "e_import"

    # don't store interval_end, it is not necessary
    interval_start = sa.Column(sa.DateTime, primary_key=True)
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
            session.query(Import)
            .filter(Import.interval_start >= from_dt)
            .order_by(sa.desc(Import.interval_start))
            .all()
        )
    except sa.exc.NoResultFound:
        log.warning("No records found in the database.")
        return
    for r in results:
        yield r


# TODO be specific about the type of data being added
def add_to_db(data: list) -> None:
    """Insert or update records in the database."""
    log.info("Adding or updating records in DB")
    for r in data:
        interval_start = to_utc_naive(r.interval_start)
        existing = (
            session.query(Import).filter_by(interval_start=interval_start).first()
        )
        if existing:
            existing.consumption = r.consumption
        else:
            entry = Import(
                interval_start=interval_start,
                consumption=r.consumption,
            )
            session.add(entry)
    try:
        session.commit()
    except sa.exc.IntegrityError:
        log.warning("Integrity error detected, rolling back the transaction.")
        session.rollback()
    else:
        log.info(f"Processed {len(data)} records in the database.")


def cleanup():
    session.close()


atexit.register(cleanup)

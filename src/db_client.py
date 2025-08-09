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

    # Meter period is 30 minutes from interval_start
    interval_start = sa.Column(sa.DateTime, primary_key=True)
    energy_kwh = sa.Column(sa.Float(precision=2))


class Export(Base):
    __tablename__ = "e_export"

    # Meter period is 30 minutes from interval_start
    interval_start = sa.Column(sa.DateTime, primary_key=True)
    energy_kwh = sa.Column(sa.Float(precision=2))


engine = sa.create_engine("sqlite:///data/energy.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def interval_start_from_most_recent_record(
    table_class: Import | Export,
) -> datetime | None:
    """If a most recent record is found, return it's interval_start, otherwise None."""
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


def get_meter_data(
    table_class: Import | Export, from_dt: datetime
) -> Generator[Import]:
    """Get records that exist after date given and return in date ascending order."""
    try:
        results = (
            session.query(table_class)
            .filter(table_class.interval_start >= from_dt)
            .order_by(sa.asc(table_class.interval_start))
            .all()
        )
    except sa.exc.NoResultFound:
        log.warning("No records found in the table %s.", table_class.__tablename__)
        return
    for r in results:
        yield r


# TODO be specific about the type of data being added
def add_to_db(table_class: Import | Export, data: list) -> None:
    """Insert or update records in the given table."""
    log.info("Adding or updating records to DB.")
    for r in data:
        interval_start = to_utc_naive(r.interval_start)
        existing = (
            session.query(table_class).filter_by(interval_start=interval_start).first()
        )
        if existing:
            existing.energy_kwh = r.energy_kwh
        else:
            entry = table_class(
                interval_start=interval_start,
                energy_kwh=r.energy_kwh,
            )
            session.add(entry)
    try:
        session.commit()
    except sa.exc.IntegrityError:
        log.warning("Integrity error detected, rolling back the transaction.")
        session.rollback()
    else:
        log.info("Added %s records to table %s.", len(data), table_class.__tablename__)


def cleanup():
    session.close()


atexit.register(cleanup)

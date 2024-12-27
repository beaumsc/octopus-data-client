import atexit
from datetime import datetime, timezone

import pytz
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

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
        return result[0]
    except sa.exc.NoResultFound:
        pass


def cleanup():
    session.close()


atexit.register(cleanup)

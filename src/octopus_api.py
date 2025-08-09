import logging
import os
from datetime import datetime

from httpx import BasicAuth, request
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from datetime_util import to_utc

log = logging.getLogger()

BASE_URL = "https://api.octopus.energy"


class ElectRec(BaseModel):
    """Electricity record from Octopus API for import and export meter points.
    Confusingly, the meter value is called 'consumption' despite being used for both
    import and export. For our use we model it 'energy_kwh'."""

    interval_start: datetime
    interval_end: datetime
    energy_kwh: float = Field(description="Usage in kWh", alias="consumption")

    @model_validator(mode="after")  # pyright: ignore
    def ensure_30min_interval(self) -> Self:
        interval = int((self.interval_end - self.interval_start).total_seconds() / 60)
        if interval != 30:
            msg = f"Invalid {interval} minutes. Only supporting 30 minute sample rate."
            raise ValueError(msg)
        return self


class Electricity(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[ElectRec]


def get_electricity_energy_kwh(
    period_from: datetime, mpan: str, sn: str
) -> list[ElectRec]:
    """Electricity units is in kWh."""

    if not isinstance(mpan, str) or not isinstance(sn, str):
        raise ValueError("MPAN and SN must be strings.")

    # The API expects period_from to have UTC timezone.
    period_from = to_utc(period_from)

    def _get_energy_kwh(url: str) -> Electricity:
        AUTH = BasicAuth(username=os.environ["api_key"], password="")
        response = request("GET", url, auth=AUTH)
        response.raise_for_status()
        page = Electricity(**response.json())
        if page.results:
            _from = page.results[-1].interval_start
            _to = page.results[0].interval_start
            log.info(
                f"Got electricity page. count={len(page.results)} from {_from} to {_to}"
            )
        else:
            log.info("Empty page results in response")
        return page

    results: list[ElectRec] = []
    url = f"{BASE_URL}/v1/electricity-meter-points/{mpan}/meters/{sn}/consumption/"
    # API expects ISO 8601 format with 'Z' for UTC
    _period_from = f"{period_from.strftime('%Y-%m-%dT%H:%M:%S')}Z"
    url += f"?period_from={_period_from}"
    while url:
        # get a page, results are in date descending order
        page = _get_energy_kwh(url)
        results.extend(page.results)
        url = page.next
    if not results:
        log.info(f"No API data available after {_period_from}")
    return results

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
    """Electricity consumption record from Octopus API."""

    interval_start: datetime
    interval_end: datetime
    consumption: float = Field(description="Usage in kWh")

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


def get_electricity_consumption(period_from: datetime) -> list[ElectRec]:
    """Electricity units is in kWh."""

    # The API expects period_from to have UTC timezone.
    period_from = to_utc(period_from)

    def _get_consumption(url: str) -> Electricity:
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
    ELECTRICITY_MPAN = os.environ["electricity_mpan"]
    ELECTRICITY_SN = os.environ["electricity_sn"]
    url = f"{BASE_URL}/v1/electricity-meter-points/{ELECTRICITY_MPAN}/meters/{ELECTRICITY_SN}/consumption/"
    # API expects ISO 8601 format with 'Z' for UTC
    _period_from = f"{period_from.strftime('%Y-%m-%dT%H:%M:%S')}Z"
    url += f"?period_from={_period_from}"
    while url:
        # get a page, results are in date descending order
        page = _get_consumption(url)
        results.extend(page.results)
        url = page.next
    if not results:
        log.info(f"No API data available after {_period_from}")
    return results


# def get_gas_consumption(after: datetime | None = None) -> list[ElectRec]:
# GAS_MPRN = os.environ["gas_mprn"]
# GAS_SN = os.environ["gas_sn"]
# URL_GAS_CONSUMPTION = (
#     f"{BASE_URL}/v1/gas-meter-points/{GAS_MPRN}/meters/{GAS_SN}/consumption/"
# )


# gas units is in cubic meters

import logging
import os
from datetime import datetime

from httpx import BasicAuth, request
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

log = logging.getLogger()

ELECTRICITY_MPAN = os.environ["electricity_mpan"]
ELECTRICITY_SN = os.environ["electricity_sn"]
GAS_MPRN = os.environ["gas_mprn"]
GAS_SN = os.environ["gas_sn"]
BASE_URL = "https://api.octopus.energy"
URL_ELECTRICITY_CONSUMPTION = f"{BASE_URL}/v1/electricity-meter-points/{ELECTRICITY_MPAN}/meters/{ELECTRICITY_SN}/consumption/"
URL_GAS_CONSUMPTION = (
    f"{BASE_URL}/v1/gas-meter-points/{GAS_MPRN}/meters/{GAS_SN}/consumption/"
)
AUTH = BasicAuth(username=os.environ["api_key"], password="")


class ElectRec(BaseModel):
    consumption: float = Field(description="Usage in kWh")
    interval_start: datetime
    interval_end: datetime

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


def get_electricity_consumption(after: datetime | None = None) -> list[ElectRec]:
    """Electricity units is in kWh"""

    def _get_consumption(url: str) -> Electricity:
        response = request("GET", url, auth=AUTH)
        response.raise_for_status()
        page = Electricity(**response.json())
        _from = page.results[-1].interval_end
        _to = page.results[0].interval_end
        log.info(
            f"got electricity page. count={ len(page.results)} from {_from} to {_to}"
        )
        return page

    url = URL_ELECTRICITY_CONSUMPTION
    results: list[ElectRec] = []
    while url:
        # get a page, results are in date descending order
        page = _get_consumption(url)
        if after and page.results[-1].interval_end <= after:
            # this page contains older entries we already have and must ignore
            results.extend([r for r in page.results if r.interval_end > after])
            break
        # else keep getting more pages of entries if more available
        results.extend(page.results)
        url = page.next

    return results


# gas units is in cubic meters

import logging
import re
import zipfile
from io import BytesIO
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

CKAN_BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_ID = "parking-tickets"
REQUEST_TIMEOUT = 120


def _get_package_resources() -> list[dict]:
    url = f"{CKAN_BASE_URL}/api/3/action/package_show"
    resp = requests.get(url, params={"id": PACKAGE_ID}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"CKAN API returned success=false for package {PACKAGE_ID}")
    return data["result"]["resources"]


def _extract_year(name: str) -> Optional[int]:
    match = re.search(r"\b(20\d{2})\b", name)
    return int(match.group(1)) if match else None


def _download_csv(resource: dict) -> pd.DataFrame:
    url = resource["url"]
    logger.info(f"Downloading from {url}")
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    content = resp.content

    fmt = resource.get("format", "").upper()
    if fmt == "ZIP" or url.lower().endswith(".zip"):
        with zipfile.ZipFile(BytesIO(content)) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError(f"No CSV found in ZIP: {url}")
            with zf.open(csv_names[0]) as f:
                return pd.read_csv(f, low_memory=False)

    return pd.read_csv(BytesIO(content), low_memory=False)


def fetch_available_years() -> list[int]:
    """Return all years available in the CKAN parking tickets package."""
    resources = _get_package_resources()
    years = []
    for r in resources:
        year = _extract_year(r.get("name", ""))
        if year:
            years.append(year)
    return sorted(set(years))


def fetch_year(year: int) -> Optional[pd.DataFrame]:
    """Download and return the parking tickets DataFrame for the given year."""
    resources = _get_package_resources()
    target = next(
        (r for r in resources if _extract_year(r.get("name", "")) == year),
        None,
    )
    if not target:
        logger.warning(f"No CKAN resource found for year {year}")
        return None

    logger.info(f"Fetching {year} parking tickets: {target['name']}")
    return _download_csv(target)

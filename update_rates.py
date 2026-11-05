import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

START = (date.today() - timedelta(days=45)).isoformat()


def latest_rate(series):
    url = (
        "https://fred.stlouisfed.org/graph/"
        f"fredgraph.csv?id={series}&cosd={START}"
    )
    request = Request(url, headers={"User-Agent": "BonjourrRateWatch/1.0"})

    with urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8-sig")

    observations = []

    for row in csv.DictReader(io.StringIO(text)):
        value = row.get(series, "").strip()
        if value in ("", "."):
            continue

        observation_date = (
            row.get("observation_date") or row.get("DATE")
        )
        if not observation_date:
            raise ValueError("Could not find the observation date.")

        observations.append(
            (date.fromisoformat(observation_date), Decimal(value))
        )

    if not observations:
        raise ValueError(f"No recent observations found for {series}.")

    return max(observations, key=lambda item: item[0])


sofr_date, sofr = latest_rate("SOFR")
prime_date, prime = latest_rate("DPRIME")

display = (
    f"Overnight SOFR: {sofr:.2f}% | Prime: {prime:.2f}%"
    f"\\nSOFR as of {sofr_date:%b %d, %Y}"
    f" | Prime as of {prime_date:%b %d, %Y}"
)

with Path("rates.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Rate Watch", display])

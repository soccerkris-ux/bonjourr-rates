import csv
import json
import re
import time
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


def download(url):
    for attempt in range(3):
        try:
            request = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 BonjourrRateWatch"},
            )
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8-sig")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)


class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)


sofr_url = (
    "https://markets.newyorkfed.org/api/"
    "rates/secured/sofr/last/1.json"
)
sofr_data = json.loads(download(sofr_url))
sofr_record = sofr_data["refRates"][0]
sofr = Decimal(str(sofr_record["percentRate"]))
sofr_date = date.fromisoformat(sofr_record["effectiveDate"])

reader = TableReader()
reader.feed(download("https://www.federalreserve.gov/releases/h15/"))

prime = None
for row in reader.rows:
    if row and "bank prime loan" in row[0].lower():
        values = [
            Decimal(cell)
            for cell in row[1:]
            if re.fullmatch(r"\d+(?:\.\d+)?", cell)
        ]
        if values:
            prime = values[-1]
            break

if prime is None:
    raise ValueError("Could not find Prime on the Federal Reserve page.")

page_text = " ".join(" ".join(reader.text).split())
release = re.search(
    r"Release date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
    page_text,
)
if not release:
    raise ValueError("Could not find the H.15 release date.")

display = (
    f"Overnight SOFR: {sofr:.2f}% | Prime: {prime:.2f}%"
    f"\\nSOFR as of {sofr_date:%b %d, %Y}"
    f" | Prime: H.15 release {release.group(1)}"
)

with Path("rates.csv").open("w", newline="", encoding="utf-8") as file:
    csv.writer(file).writerow(["Rate Watch", display])

print(f"Created rates.csv: {display}")

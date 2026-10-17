"""Dohvaća povijest indeksa s Yahoo Finance i zapisuje docs/data.json.

Novi indeks dodaje se jednim retkom u INDICES (Yahoo simbol, naziv, kratki opis).
Pokretanje: python scripts/fetch_data.py  (bez dodatnih paketa)
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

INDICES = [
    ("^GSPC", "S&P 500", "Cjenovni indeks"),
    ("^SP500TR", "S&P 500 TR", "S dividendama"),
    ("^IXIC", "Nasdaq Composite", "Cjenovni indeks"),
    ("^NDX", "Nasdaq 100", "Cjenovni indeks"),
    # Primjeri za kasnije:
    # ("^DJI", "Dow Jones", "Cjenovni indeks"),
    # ("^GDAXI", "DAX", "Total return"),
    # ("^STOXX50E", "Euro Stoxx 50", "Cjenovni indeks"),
    # ("^FTSE", "FTSE 100", "Cjenovni indeks"),
    # ("^N225", "Nikkei 225", "Cjenovni indeks"),
]

YEARS = (3, 5, 10)
OUT = Path(__file__).resolve().parent.parent / "docs" / "data.json"
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}?range=11y&interval=1d"


def fetch(symbol):
    req = urllib.request.Request(
        URL.format(urllib.parse.quote(symbol)), headers={"User-Agent": "Mozilla/5.0"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["chart"]["result"][0]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def years_ago(d, n):
    try:
        return d.replace(year=d.year - n)
    except ValueError:  # 29. veljače
        return d.replace(year=d.year - n, day=28)


def close_on_or_before(series, target):
    """Zadnja zaključna cijena na dan target ili prije njega."""
    best = None
    for d, c in series:
        if d > target:
            break
        best = (d, c)
    return best


def pct(now, base):
    return round((now / base - 1) * 100, 2)


def compute(symbol, name, note):
    res = fetch(symbol)
    tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
    closes = res["indicators"]["quote"][0]["close"]
    series = [
        (datetime.fromtimestamp(t, tz).date(), c)
        for t, c in zip(res["timestamp"], closes)
        if c is not None
    ]
    last_d, last = series[-1]
    prev = series[-2][1]

    periods = {}
    ytd_base = close_on_or_before(series, date(last_d.year - 1, 12, 31))
    periods["ytd"] = {"pct": pct(last, ytd_base[1]), "from": ytd_base[0].isoformat()}
    for n in YEARS:
        base = close_on_or_before(series, years_ago(last_d, n))
        if base is None:
            continue
        total = last / base[1]
        periods[f"{n}y"] = {
            "pct": pct(last, base[1]),
            "pa": round((total ** (1 / n) - 1) * 100, 2),
            "from": base[0].isoformat(),
        }

    return {
        "symbol": symbol,
        "name": name,
        "note": note,
        "last": round(last, 2),
        "date": last_d.isoformat(),
        "day": pct(last, prev),
        "periods": periods,
    }


def main():
    out, errors = [], []
    for sym, name, note in INDICES:
        try:
            out.append(compute(sym, name, note))
        except Exception as e:
            errors.append(f"{sym}: {e}")
    if not out:
        raise SystemExit("Nijedan indeks nije dohvaćen: " + "; ".join(errors))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "indices": out,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"OK: {len(out)} indeksa, greške: {errors or 'nema'}")


if __name__ == "__main__":
    main()

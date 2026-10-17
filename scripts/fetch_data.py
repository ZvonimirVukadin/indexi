"""Dohvaća povijest indeksa s Yahoo Finance i zapisuje docs/data.json.

Novi indeks dodaje se jednim retkom u INDICES (Yahoo simbol, naziv, kratki opis).
Pokretanje: python scripts/fetch_data.py  (bez dodatnih paketa)
"""
import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

INDICES = [
    ("^GSPC", "S&P 500", "Cjenovni indeks"),
    ("^SP500TR", "S&P 500 TR", "S dividendama"),
    ("^GDAXI", "DAX", "S dividendama, u EUR"),
    ("^NDX", "Nasdaq 100", "Cjenovni indeks"),
    # Primjeri za kasnije:
    # ("^DJI", "Dow Jones", "Cjenovni indeks"),
    # ("^IXIC", "Nasdaq Composite", "Cjenovni indeks"),
    # ("^STOXX50E", "Euro Stoxx 50", "Cjenovni indeks"),
    # ("^FTSE", "FTSE 100", "Cjenovni indeks"),
    # ("^N225", "Nikkei 225", "Cjenovni indeks"),
]

# Fondovi čiji se prinosi preuzimaju sa stranice društva (prikazuju se na vrhu tablice usporedbe)
FUNDS = [
    ("capital-breeder", "Capital Breeder", "https://globalinvest.hr/capital-breeder/"),
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


def page_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        s = r.read().decode("utf-8", "replace")
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", "\n", s))
    return [l.strip() for l in s.splitlines() if l.strip()]


def hr_num(s):
    return float(s.replace("%", "").replace("EUR", "").replace(".", "").replace(",", ".").strip())


def compute_fund(key, name, url):
    """Prinosi Global Invest fonda: 'Prinos u <godina>' (YTD) i 'PGP N' (prosječni godišnji prinos)."""
    lines = page_text(url)

    def after(pattern):
        for i, l in enumerate(lines[:-1]):
            if re.fullmatch(pattern, l):
                return lines[i + 1]
        raise ValueError(f"nije pronađeno: {pattern}")

    periods = {"ytd": {"pct": round(hr_num(after(r"Prinos u \d{4}")), 2)}}
    for n in YEARS:
        pa = hr_num(after(f"PGP {n}"))
        periods[f"{n}y"] = {"pct": round(((1 + pa / 100) ** n - 1) * 100, 2), "pa": round(pa, 2)}
    i = lines.index("Vrijednost udjela")
    d = datetime.strptime(lines[i + 2], "%d.%m.%Y").date()
    return {
        "symbol": key,
        "name": name,
        "note": "Fond, u EUR",
        "last": hr_num(lines[i + 1]),
        "date": d.isoformat(),
        "periods": periods,
    }


def main():
    out, funds, errors = [], [], []
    for sym, name, note in INDICES:
        try:
            out.append(compute(sym, name, note))
        except Exception as e:
            errors.append(f"{sym}: {e}")
    if not out:
        raise SystemExit("Nijedan indeks nije dohvaćen: " + "; ".join(errors))
    try:
        old = {f["symbol"]: f for f in json.loads(OUT.read_text(encoding="utf-8")).get("funds", [])}
    except Exception:
        old = {}
    for key, name, url in FUNDS:
        try:
            funds.append(compute_fund(key, name, url))
        except Exception as e:
            errors.append(f"{name}: {e}")
            if key in old:  # zadrži zadnje poznate podatke
                funds.append(old[key])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "indices": out,
                "funds": funds,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"OK: {len(out)} indeksa, {len(funds)} fondova, greške: {errors or 'nema'}")


if __name__ == "__main__":
    main()

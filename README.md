# Indeksi – brzi pregled promjena (YTD, 3, 5, 10 god.)

Mala web-aplikacija za iPhone: S&P 500, S&P 500 TR (s dividendama), Nasdaq Composite i Nasdaq 100,
promjene u postotku na dvije decimale. Za 3/5/10 godina prikazan je i prosječni godišnji prinos.

## Kako radi
- `scripts/fetch_data.py` dohvaća povijest s Yahoo Finance i zapisuje `docs/data.json`.
- GitHub Actions (`.github/workflows/update.yml`) to pokreće svakih 30 min tijekom US trgovanja i nakon zatvaranja.
- GitHub Pages poslužuje `docs/` kao web stranicu. Sve je besplatno.

## Postavljanje (jednokratno, ~5 min)
1. Napravite besplatan račun na github.com i novi **javni** repozitorij, npr. `indeksi`.
2. Učitajte sadržaj ove mape (Add file → Upload files, uključujući mapu `.github`), ili preko gita:
   ```
   git remote add origin https://github.com/<korisnik>/indeksi.git
   git push -u origin main
   ```
3. Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, mapa `/docs` → Save.
4. Actions → „Ažuriranje podataka” → *Run workflow* (prvo ručno pokretanje).
5. Na iPhoneu u Safariju otvorite `https://<korisnik>.github.io/indeksi/` → Dijeli → **Dodaj na početni zaslon**.

## Dodavanje novih indeksa
U `scripts/fetch_data.py` u listu `INDICES` dodajte redak s Yahoo simbolom (primjeri: `^DJI`, `^GDAXI`,
`^STOXX50E`, `^FTSE`, `^N225` su već upisani kao komentari – samo maknite `#`).

## Napomene
- YTD se računa od zaključne cijene zadnjeg trgovinskog dana prošle godine; 3/5/10 god. od zaključne
  cijene na isti datum (ili zadnji trgovinski dan prije) prije N godina.
- Yahoo Finance je neslužbeni besplatni izvor; ako ikad prestane raditi, mijenja se samo `fetch_data.py`.

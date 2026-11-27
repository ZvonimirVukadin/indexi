# Indeksi – brzi pregled promjena (YTD, 3, 5, 10 god.)

Mala web-aplikacija za iPhone: S&P 500, S&P 500 TR (s dividendama), Nasdaq Composite i Nasdaq 100,
promjene u postotku na dvije decimale. Za 3/5/10 godina prikazan je i prosječni godišnji prinos.

## Kako radi
- `scripts/fetch_data.py` dohvaća povijest s Yahoo Finance i zapisuje `docs/data.json`.
- GitHub Actions (`.github/workflows/update.yml`) to pokreće kad ga pozove vanjski cron (cron-job.org):
  radnim danom svakih 30 min tijekom US trgovanja i svaki dan u 13:00 po zagrebačkom vremenu.
  GitHubov vlastiti raspored ostao je samo kao rezerva jer kasni i po nekoliko sati.
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

## Točni termini ažuriranja (vanjski okidač, jednokratno ~10 min)
GitHubov `schedule` kasni satima, a ručno pokretanje (`workflow_dispatch`) krene odmah. Zato ga
besplatni servis cron-job.org poziva preko GitHub API-ja u zadanim terminima.

1. **Token na GitHubu:** Settings → Developer settings → Personal access tokens → *Fine-grained tokens* →
   *Generate new token*.
   - Repository access: *Only select repositories* → ovaj repozitorij.
   - Permissions → Repository permissions → **Actions: Read and write** (ništa drugo).
   - Expiration: najdulje ponuđeno; zapišite datum isteka – tada treba napraviti novi token.
2. **Račun na cron-job.org**, zatim *Create cronjob* za svaki termin:

   | Posao | Vremenska zona | Dani | Sati | Minute |
   |---|---|---|---|---|
   | Indeksi 13:00 | Europe/Zagreb | svaki dan | 13 | 0 |
   | Indeksi US | America/New_York | pon–pet | 10–16 | 0, 30 |

   „Indeksi US” radi od 10:00 do 16:30 po njujorškom vremenu, a zadnji poziv uhvati zaključne cijene.
   Zona America/New_York sama prati američki prelazak na ljetno vrijeme.

   Za oba posla isti zahtjev (kartica *Advanced*):
   - URL: `https://api.github.com/repos/<korisnik>/<repozitorij>/actions/workflows/update.yml/dispatches`
   - Request method: **POST**
   - Headers:
     - `Authorization: Bearer <token iz koraka 1>`
     - `Accept: application/vnd.github+json`
     - `X-GitHub-Api-Version: 2022-11-28`
     - `Content-Type: application/json`
   - Request body: `{"ref":"main"}`
   - Uključite obavijest e-poštom kad poziv ne uspije, tako ćete saznati i kad token istekne.
3. **Provjera:** *Test run* u cron-job.org treba vratiti **HTTP 204**, a na GitHubu pod Actions se odmah
   pojavi novo pokretanje s oznakom *workflow_dispatch*.

## Dodavanje novih indeksa
U `scripts/fetch_data.py` u listu `INDICES` dodajte redak s Yahoo simbolom (primjeri: `^DJI`, `^GDAXI`,
`^STOXX50E`, `^FTSE`, `^N225` su već upisani kao komentari – samo maknite `#`).

## Napomene
- YTD se računa od zaključne cijene zadnjeg trgovinskog dana prošle godine; 3/5/10 god. od zaključne
  cijene na isti datum (ili zadnji trgovinski dan prije) prije N godina.
- Yahoo Finance je neslužbeni besplatni izvor; ako ikad prestane raditi, mijenja se samo `fetch_data.py`.

# Laborator 2 — înregistrarea proprietăților filmelor în Recombee

Proiect Python pentru definirea proprietăților unui catalog de filme prin SDK-ul oficial Recombee. Scriptul verifică dataset-ul, creează proprietățile lipsă și confirmă prin API tipurile salvate.

**Integrare verificată pe 22 octombrie 2026:** cele șapte proprietăți au fost create în baza de dezvoltare, iar numele și tipurile au fost confirmate printr-un nou apel `ListItemProperties`. Raportul rezultat este păstrat local în `reports/recombee_properties.json`. Validarea locală și cele 12 teste au trecut. Invitația profesorului și predarea pe Moodle se fac conform secțiunilor 7 și 9.

## 1. Dataset-ul ales

- **Domeniu:** filme; un item reprezintă un film.
- **Sursă:** [Movies Dataset pe Kaggle](https://www.kaggle.com/datasets/akshaydattatraykhare/movies-dataset), publicat de Akshay Dattatray Khare.
- **Fișier folosit:** [`archive-3/tmdb_5000_movies.csv`](archive-3/tmdb_5000_movies.csv).
- **Volum verificat:** 4.803 filme, 20 de coloane și 4.803 identificatori unici. Se respectă intervalul 100–10.000 de item-uri.
- **Date originale:** CSV-ul este păstrat integral, exact cum a fost furnizat în arhivă. Nu se elimină rânduri, nu se redenumesc coloane și nu se completează valori.

Arhiva conține și `tmdb_5000_credits.csv` (4.803 rânduri), cu distribuția și echipa filmelor. Acest fișier rămâne neschimbat și nu este folosit de scriptul laboratorului 2. Nu trebuie combinat cu fișierul de filme.

Conform descrierii autorului de pe Kaggle, datele provin din API-ul The Movie Database (TMDb). Pagina Kaggle indică licența „Other (specified in description)”; păstrăm sursa și atribuirea, fără să atribuim dataset-ului o altă licență. Dataset-ul folosește API-ul TMDb și nu este aprobat sau certificat de TMDb.

### Proprietățile înregistrate în Recombee

Laboratorul cere minimum trei proprietăți. Proiectul definește următoarele șapte, folosind numele originale din CSV:

| Coloană | Tip Recombee | Semnificație | Exemplu pentru Avatar |
| --- | --- | --- | --- |
| `title` | `string` | Titlul filmului | `Avatar` |
| `original_language` | `string` | Codul limbii originale | `en` |
| `budget` | `int` | Bugetul raportat în dataset | `237000000` |
| `revenue` | `int` | Încasările raportate în dataset | `2787965087` |
| `popularity` | `double` | Scorul de popularitate din sursă | `150.437577` |
| `vote_average` | `double` | Media voturilor, pe scala 0–10 | `7.2` |
| `vote_count` | `int` | Numărul de voturi | `11800` |

`id` este identificatorul TMDb al filmului. **Nu se înregistrează ca proprietate.** La încărcarea filmelor în laboratorul următor, valoarea lui va fi folosită ca `itemId`, de exemplu `"19995"` pentru Avatar.

Celelalte coloane rămân în CSV. Unele au celule goale sau liste în format JSON; nu sunt necesare pentru schema acestui laborator. Cele șapte proprietăți alese și `id` nu au valori lipsă în fișierul verificat. Valorile zero din `budget` și `revenue` se păstrează exact ca în sursă; nu sunt înlocuite cu estimări.

### Integritatea fișierelor

Amprentele SHA-256 ale fișierelor furnizate:

```text
tmdb_5000_movies.csv
1e0584a8dd374120e4ed4f2b81f0d2bd0eb95a554708e4a350d00ed5c46d2825

tmdb_5000_credits.csv
9d0050599ff88d40366c4841204b1489862bca346bfa46c20b05a65d14508435
```

Pe macOS poți verifica amprentele cu:

```bash
shasum -a 256 archive-3/*.csv
```

## 2. Pregătirea mediului Python

Deschide terminalul în folderul `lab02_sr`. Este recomandat Python 3.11 sau mai nou; codul este compatibil și cu Python 3.9.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Dependențele sunt SDK-ul oficial `recombee-api-client`, `pandas` pentru citirea CSV-ului și `python-dotenv` pentru configurația locală. Nu ai nevoie de `kagglehub`: dataset-ul este deja în proiect. Codul de descărcare primit de pe Kaggle este necesar numai când fișierele nu sunt încă descărcate.

## 3. Verificarea locală, înainte de crearea contului

Cu mediul virtual activat:

```bash
python recombee_properties.py --dry-run
```

Rezultatul trebuie să înceapă cu:

```text
Dataset valid: 4803 filme, ID-uri unice, 7 proprietăți.
```

Scriptul afișează primele trei filme și schema. În acest mod nu se conectează la Recombee și nu cere token. Verifică volumul, coloanele necesare, ID-urile unice, valorile obligatorii și tipurile numerice. Citește CSV-ul fără să-l rescrie.

## 4. Crearea contului și a bazei Recombee

1. Intră pe [recombee.com](https://www.recombee.com/) și selectează **Start Free**.
2. Creează contul cu adresa ta de e-mail și finalizează verificarea cerută de platformă.
3. Deschide [Recombee Admin UI](https://admin.recombee.com/).
4. Urmează configurarea inițială a organizației și creează sau selectează o bază de date pentru laborator. Poți folosi un nume precum `lab02-movies`, dacă este disponibil.
5. La alegerea regiunii poți selecta Europa (`eu-west`). Pentru o bază existentă folosește regiunea ei reală.
6. În **Settings → API Logins**, identifică **Database ID**, **Private Token** și regiunea bazei. Folosește valorile afișate de contul tău, inclusiv orice sufix al Database ID.

Pentru definirea proprietăților este necesar tokenul **privat**, cu acces de scriere la baza selectată.

## 5. Configurarea fișierului `.env`

Pe macOS / Linux:

```bash
cp .env.example .env
```

Pe Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Deschide `.env` în editor și înlocuiește valorile demonstrative:

```dotenv
RECOMBEE_DATABASE_ID=completeaza_database_id
RECOMBEE_PRIVATE_TOKEN=completeaza_private_token
RECOMBEE_REGION=eu-west
```

Fișierul `.env` este exclus din Git prin `.gitignore`. În repository se urcă doar `.env.example`, fără tokenul real. Nu pune tokenul în cod, capturi de ecran sau README. Dacă ai deja variabilele configurate în terminal, acestea au prioritate față de `.env`.

## 6. Înregistrarea și verificarea proprietăților

```bash
python recombee_properties.py
```

Scriptul execută următorii pași:

1. Validează catalogul local.
2. Citește configurația și inițializează clientul oficial Recombee.
3. Folosește `ListItemProperties` pentru a vedea schema existentă.
4. Verifică tipurile proprietăților existente înainte de a crea ceva.
5. Trimite `AddItemProperty` pentru fiecare proprietate lipsă.
6. Apelează din nou `ListItemProperties` și confirmă numele și tipurile celor șapte proprietăți.
7. Salvează rezultatul verificării în `reports/recombee_properties.json`, fără token.

La final trebuie să apară:

```text
Confirmat prin API: toate cele 7 proprietăți au tipurile corecte.
```

Poți relua comanda. Proprietățile existente cu tipul corect sunt păstrate. Dacă o proprietate are un tip diferit, scriptul se oprește și indică diferența. O eroare produce un cod de ieșire diferit de zero. Dacă o cerere eșuează după crearea unor proprietăți, acestea rămân în Recombee; reluarea comenzii continuă cu proprietățile lipsă.

Pentru verificare prin API, fără a crea proprietăți:

```bash
python recombee_properties.py --verify-only
```

În Admin UI, deschide **Items**, apoi **Manage properties** și verifică cele șapte nume și tipuri din tabelul de mai sus. În acest laborator definim schema; încărcarea rândurilor de filme se face în laboratorul următor. Prin urmare, catalogul poate avea încă zero item-uri.

## 7. Accesul profesorului

1. În Recombee Admin UI, mergi la **Settings → Organization Users**.
2. Apasă **Invite User**.
3. Introdu adresa de e-mail indicată de profesor.
4. Acordă dreptul **Edit** pentru baza de date folosită la laborator.
5. Trimite invitația și verifică permisiunea configurată.

Conform cerinței laboratorului, profesorul are nevoie de **Edit** pentru a putea citi sau genera chei de test dacă apar erori de autentificare.

## 8. Publicarea pe GitHub

Repository-ul proiectului este [Antonio0805/lab02-recombee-movies](https://github.com/Antonio0805/lab02-recombee-movies) și are vizibilitatea **Public**. Profesorul poate consulta codul și dataset-ul fără invitație pe GitHub. Invitația în Recombee, cu dreptul **Edit** pe baza de date, rămâne necesară conform secțiunii 7.

Pentru a descărca proiectul pe alt calculator:

```bash
git clone https://github.com/Antonio0805/lab02-recombee-movies.git
cd lab02-recombee-movies
```

Pentru modificări ulterioare, din folderul proiectului:

```bash
git add README.md requirements.txt recombee_properties.py .env.example .gitignore .gitattributes tests archive-3
git status
git commit -m "Actualizeaza proiectul laboratorului 2"
git push -u origin main
```

Verifică înainte de commit că `.env` și `.venv` nu apar printre fișierele pregătite pentru publicare. Fișierul de filme are aproximativ 5,7 MB, iar cel de credite aproximativ 40 MB; ele sunt fișierele originale furnizate.

## 9. Predarea pe Moodle

Fișierul local `predare.txt` conține **o singură linie: linkul repository-ului**:

```text
https://github.com/Antonio0805/lab02-recombee-movies
```

Încarcă pe Moodle fișierul `.txt`, fără explicații sau cod în interiorul lui. Fișierul de predare este exclus din Git și se găsește în folderul local al proiectului.

## 10. Verificări și erori frecvente

Testele locale, cu API simulat, se rulează astfel:

```bash
python -m unittest discover -s tests -v
```

Aceste teste verifică validarea datelor și comportamentul scriptului; confirmarea integrării reale se obține prin rularea cu datele contului tău.

| Mesaj / situație | Rezolvare |
| --- | --- |
| `ModuleNotFoundError` | Activează `.venv` și rulează `python -m pip install -r requirements.txt`. |
| `Completează RECOMBEE_...` | Copiază `.env.example` în `.env` și introdu datele reale. |
| HTTP 401 / 403 | Verifică Database ID, tokenul privat, regiunea și accesul de scriere. |
| Un tip existent diferă de cel cerut | Verifică baza selectată și proprietatea indicată. Scriptul nu șterge proprietăți. |
| CSV negăsit | Păstrează folderul `archive-3` lângă script sau folosește `--dataset CALE_CSV`. |
| `NotOpenSSLWarning` pe Python-ul de sistem macOS | Folosește Python 3.11+ instalat separat și recreează mediul virtual cu acel interpret. |

### Corespondența cu baremul

| Criteriu | Livrabil / verificare |
| --- | --- |
| Dataset CSV cu 100–10.000 de item-uri — 30p | Fișierul original cu 4.803 filme |
| Domeniu și minimum 3 proprietăți documentate — 20p | Secțiunea 1, tabel cu 7 proprietăți și tipurile lor |
| Script adaptat și funcțional — 30p | `recombee_properties.py`, dependențe și verificări locale |
| Proprietăți integrate în Recombee — 20p | Cele 7 proprietăți au fost create și confirmate prin API în baza de dezvoltare; pot fi consultate în Admin UI |

## Referințe

- [Cerințele laboratorului și codul de pornire](https://github.com/GG-Academy/Recommender-Systems/tree/main/lab02)
- [Dataset-ul ales de pe Kaggle](https://www.kaggle.com/datasets/akshaydattatraykhare/movies-dataset)
- [SDK-ul oficial Python Recombee](https://docs.recombee.com/python_client)
- [API pentru proprietățile item-urilor](https://docs.recombee.com/api/item-properties)
- [Regiunile Recombee](https://docs.recombee.com/regions)

# Laborator 2: Catalog de filme în Recombee

Pentru acest laborator am ales să lucrez cu un catalog de filme de pe Kaggle. Am folosit Python și SDK-ul oficial Recombee pentru a înregistra proprietățile filmelor în baza de date.

Scopul acestei etape este să pregătesc structura catalogului. Am definit șapte proprietăți și am verificat prin API că fiecare are tipul de date corect. Încărcarea filmelor în Recombee se va face în laboratorul următor.

## Dataset-ul ales

Am folosit [Movies Dataset](https://www.kaggle.com/datasets/akshaydattatraykhare/movies-dataset), publicat pe Kaggle de Akshay Dattatray Khare. Datele provin din The Movie Database (TMDb).

| Detaliu | Valoare |
| --- | --- |
| Domeniu | Filme |
| Fișier folosit | [`archive-3/tmdb_5000_movies.csv`](archive-3/tmdb_5000_movies.csv) |
| Număr de filme | 4.803 |
| Număr de coloane | 20 |
| Identificator unic | `id`, identificatorul TMDb al filmului |

Am păstrat fișierul CSV exact cum l-am descărcat: cu toate rândurile, numele originale ale coloanelor și valorile din sursă. Cele 4.803 filme se încadrează în limita de 100 până la 10.000 de item-uri cerută la laborator.

În folder se află și `tmdb_5000_credits.csv`, care conține informații despre actori și echipele filmelor. L-am păstrat în forma originală, dar pentru această etapă folosesc doar fișierul de filme.

## Proprietățile înregistrate

Din coloanele existente am ales următoarele șapte proprietăți. Toate au valori completate în dataset.

| Proprietate | Tip Recombee | Ce reprezintă | Exemplu pentru Avatar |
| --- | --- | --- | --- |
| `title` | `string` | Titlul filmului | `Avatar` |
| `original_language` | `string` | Codul limbii originale | `en` |
| `budget` | `int` | Bugetul raportat în dataset | `237000000` |
| `revenue` | `int` | Încasările raportate în dataset | `2787965087` |
| `popularity` | `double` | Scorul de popularitate | `150.437577` |
| `vote_average` | `double` | Media voturilor, între 0 și 10 | `7.2` |
| `vote_count` | `int` | Numărul de voturi | `11800` |

`string` înseamnă text, `int` este un număr întreg, iar `double` este un număr care poate avea zecimale.

Am păstrat coloana `id` în CSV. La importul filmelor voi folosi valoarea ei ca `itemId`, identificatorul gestionat nativ de Recombee. De exemplu, Avatar are ID-ul `19995`. Conform cerinței laboratorului, nu am înregistrat `id` ca proprietate.

Celelalte coloane rămân în fișier, inclusiv cele cu celule goale sau liste în format JSON. Am păstrat și valorile zero din `budget` și `revenue`, fără să le înlocuiesc cu estimări.

## Ce face scriptul

Am organizat implementarea în fișierul [`recombee_properties.py`](recombee_properties.py). La rulare, scriptul:

1. Citește CSV-ul și verifică numărul de filme, coloanele necesare și unicitatea ID-urilor.
2. Verifică valorile celor șapte proprietăți și tipurile numerice.
3. Citește configurația din `.env` și se conectează la Recombee.
4. Folosește `ListItemProperties` pentru a verifica proprietățile existente.
5. Creează proprietățile lipsă cu `AddItemProperty`.
6. Citește din nou schema din Recombee și confirmă numele și tipurile proprietăților.

După confirmare, salvează un raport local în `reports/recombee_properties.json`. Scriptul citește dataset-ul fără să rescrie CSV-ul.

Pot rula scriptul de mai multe ori. Dacă proprietățile există deja cu tipul corect, le păstrează. Dacă găsește un tip diferit, se oprește și afișează problema. În cazul unei întreruperi, pot relua comanda pentru a crea proprietățile rămase.

## Fișierele proiectului

```text
lab02-recombee-movies/
├── archive-3/
│   ├── tmdb_5000_movies.csv      # Catalogul folosit
│   └── tmdb_5000_credits.csv     # Date suplimentare din arhiva originală
├── tests/
│   └── test_recombee_properties.py
├── recombee_properties.py       # Scriptul pentru laborator
├── requirements.txt             # Bibliotecile necesare
├── .env.example                 # Model pentru configurația locală
├── .gitignore
├── .gitattributes
└── README.md
```

Fișierele `.env`, `predare.txt` și folderul `reports` sunt locale și sunt excluse din Git. Modelul `.env.example` este inclus în repository.

## Instalare și configurare

Am folosit bibliotecile `pandas`, `recombee-api-client` și `python-dotenv`. Versiunile sunt trecute în `requirements.txt`. Recomand Python 3.11 sau mai nou; am verificat proiectul și pe Python 3.9.

### 1. Descărcarea proiectului

```bash
git clone https://github.com/Antonio0805/lab02-recombee-movies.git
cd lab02-recombee-movies
```

### 2. Pregătirea mediului Python

Pe macOS sau Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Pe Windows, în PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Dataset-ul este deja în repository, deci nu trebuie descărcat din nou și nu este nevoie de `kagglehub` pentru rulare.

### 3. Conectarea la Recombee

Am creat un cont [Recombee](https://www.recombee.com/) și am folosit baza de dezvoltare, cu regiunea Europa (`eu-west`). Datele de conectare se găsesc în [Admin UI](https://admin.recombee.com/), la **Settings → API Logins**.

La prima configurare, copiez `.env.example` într-un fișier numit `.env`:

```bash
cp .env.example .env
```

Pe Windows folosesc `Copy-Item .env.example .env`. Dacă fișierul `.env` este deja configurat, îl păstrez.

În `.env` completez valorile din contul propriu:

```dotenv
RECOMBEE_DATABASE_ID=completeaza_database_id
RECOMBEE_PRIVATE_TOKEN=completeaza_private_token
RECOMBEE_REGION=eu-west
```

Folosesc tokenul privat pentru a putea crea proprietățile. Fișierul `.env` este exclus prin `.gitignore`, astfel că tokenul rămâne doar pe calculatorul meu. Variabilele de mediu deja setate în terminal au prioritate față de valorile din fișier.

## Rularea proiectului

Rulez comenzile din folderul proiectului, cu mediul virtual activat.

### Verificarea dataset-ului

```bash
python recombee_properties.py --dry-run
```

Această comandă verifică datele local și afișează primele trei filme. Funcționează fără cont sau token Recombee. Rezultatul începe cu:

```text
Dataset valid: 4803 filme, ID-uri unice, 7 proprietăți.
```

### Înregistrarea proprietăților în Recombee

```bash
python recombee_properties.py
```

La finalul unei rulări reușite apare mesajul:

```text
Confirmat prin API: toate cele 7 proprietăți au tipurile corecte.
```

### Verificarea proprietăților existente

```bash
python recombee_properties.py --verify-only
```

Folosesc această comandă pentru a verifica schema prin API, fără să creez proprietăți. Pot vedea aceleași proprietăți și în Admin UI, la **Items → Manage properties**.

Dacă fișierul CSV se află în alt folder, pot indica locația lui prin `--dataset CALE_CSV`.

## Rezultatele obținute

Am verificat integrarea pe 22 octombrie 2026. Cele șapte proprietăți există în Recombee și au tipurile din tabel. Am verificat și în Admin UI lista proprietăților.

Am rulat cele 12 teste locale, iar toate au trecut:

```bash
python -m unittest discover -s tests -v
```

Testele verifică validarea datelor, păstrarea fișierelor originale și comportamentul scriptului cu un API simulat. Separat, am rulat verificarea pe baza reală Recombee.

Am configurat accesul profesorului cu dreptul **Edit** pe baza folosită la laborator. Această permisiune îi permite să verifice integrarea și să acceseze cheile de test, conform cerinței.

Catalogul afișează momentan **0 item-uri**. Pentru laboratorul 2 am creat schema; importul celor 4.803 filme urmează în laboratorul următor.

## Probleme care pot apărea la rulare

| Situație | Ce verific |
| --- | --- |
| `ModuleNotFoundError` | Activez mediul virtual și instalez pachetele din `requirements.txt`. |
| Mesajul cere o variabilă `RECOMBEE_...` | Completez și salvez `.env`. |
| Eroare HTTP 401 sau 403 | Verific Database ID, tokenul privat, regiunea și accesul de scriere. |
| O proprietate are alt tip | Verific baza selectată și proprietatea indicată în mesaj. |
| Fișierul CSV nu este găsit | Verific folderul `archive-3` sau folosesc opțiunea `--dataset`. |
| `NotOpenSSLWarning` pe macOS | Folosesc Python 3.11+ instalat separat și recreez mediul virtual. |

## Predarea

Am publicat codul și dataset-ul în repository-ul [lab02-recombee-movies](https://github.com/Antonio0805/lab02-recombee-movies), care este public.

Pentru Moodle am pregătit fișierul local `predare.txt`. Acesta conține exclusiv linkul repository-ului:

```text
https://github.com/Antonio0805/lab02-recombee-movies
```

La predare încarc fișierul `.txt` pe Moodle și verific că platforma a salvat trimiterea.

## Surse

- [Cerințele laboratorului 2](https://github.com/GG-Academy/Recommender-Systems/tree/main/lab02)
- [Movies Dataset pe Kaggle](https://www.kaggle.com/datasets/akshaydattatraykhare/movies-dataset)
- [SDK-ul Python Recombee](https://docs.recombee.com/python_client)
- [Documentația API pentru proprietăți](https://docs.recombee.com/api/item-properties)

Pagina Kaggle indică licența "Other (specified in description)". Conform descrierii autorului, dataset-ul folosește API-ul TMDb și nu este aprobat sau certificat de TMDb.

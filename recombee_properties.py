"""Laborator 2: validarea catalogului și înregistrarea proprietăților Recombee."""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddItemProperty, ListItemProperties
from recombee_api_client.exceptions import APIException
from requests.exceptions import RequestException

ROOT = Path(__file__).resolve().parent
PATH_DATASET = ROOT / "archive-3" / "tmdb_5000_movies.csv"
# id din CSV va fi folosit ca itemId; NU este proprietate de catalog.
PROPRIETATI_CATALOG = [
    {"name": "title", "type": "string"},
    {"name": "original_language", "type": "string"},
    {"name": "budget", "type": "int"},
    {"name": "revenue", "type": "int"},
    {"name": "popularity", "type": "double"},
    {"name": "vote_average", "type": "double"},
    {"name": "vote_count", "type": "int"},
]
REGIONS = {
    "eu-west": Region.EU_WEST,
    "us-west": Region.US_WEST,
    "ca-east": Region.CA_EAST,
    "ap-se": Region.AP_SE,
}


def load_dataset(dataset_path=PATH_DATASET):
    """Oprește rularea înainte de API dacă datele nu respectă schema."""
    df = pd.read_csv(dataset_path, dtype=str, keep_default_na=False)
    expected_columns = {"id", *(p["name"] for p in PROPRIETATI_CATALOG)}
    missing_columns = expected_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Lipsesc coloanele obligatorii: {sorted(missing_columns)}")
    if not 100 <= len(df) <= 10_000:
        raise ValueError(f"CSV-ul are {len(df)} rânduri; sunt permise 100–10.000.")
    for name in expected_columns:
        if df[name].str.strip().eq("").any():
            raise ValueError(f"Coloana {name} conține valori lipsă.")
    if not df["id"].str.fullmatch(r"[1-9][0-9]*").all():
        raise ValueError("id trebuie să conțină identificatori întregi pozitivi.")
    if df["id"].duplicated().any():
        raise ValueError("CSV-ul conține identificatori id duplicați.")
    # Conversiile de mai jos verifică valorile doar în memorie. CSV-ul nu este rescris.
    for prop in PROPRIETATI_CATALOG:
        name, prop_type = prop["name"], prop["type"]
        if prop_type == "int":
            if not df[name].str.fullmatch(r"[0-9]+").all():
                raise ValueError(f"Coloana {name} trebuie să conțină întregi nenegativi.")
            if not df[name].map(lambda value: int(value) <= 2**63 - 1).all():
                raise ValueError(f"Coloana {name} depășește limita întregilor pe 64 de biți.")
        elif prop_type == "double":
            numeric = pd.to_numeric(df[name], errors="raise")
            if not (numeric.map(math.isfinite) & numeric.ge(0)).all():
                raise ValueError(f"Coloana {name} trebuie să conțină numere finite nenegative.")
            if name == "vote_average" and not numeric.le(10).all():
                raise ValueError("vote_average trebuie să fie între 0 și 10.")
    print(f"Dataset valid: {len(df)} filme, ID-uri unice, {len(PROPRIETATI_CATALOG)} proprietăți.")
    preview_columns = ["id", *(p["name"] for p in PROPRIETATI_CATALOG)]
    print(df[preview_columns].head(3).to_string(index=False))
    return df


def check_property_types(active_properties, require_all=False):
    """Verifică tipurile tuturor proprietăților înainte de orice modificare."""
    active = {prop["name"]: prop["type"] for prop in active_properties}
    for prop in PROPRIETATI_CATALOG:
        name, expected_type = prop["name"], prop["type"]
        if name in active and active[name] != expected_type:
            raise ValueError(
                f"Proprietatea {name} există cu tipul {active[name]}, "
                f"dar proiectul cere {expected_type}. Verifică baza selectată."
            )
        if require_all and name not in active:
            raise ValueError(f"Lipsește proprietatea {name} din Recombee.")
    return active


def set_properties(client):
    """Creează numai proprietățile lipsă; poate fi apelată repetat."""
    active = check_property_types(client.send(ListItemProperties()))
    for prop in PROPRIETATI_CATALOG:
        name, prop_type = prop["name"], prop["type"]
        if name in active:
            print(f"Există deja: {name} ({prop_type}).")
            continue
        client.send(AddItemProperty(name, prop_type))
        print(f"Creată: {name} ({prop_type}).")


def verify(client):
    """Confirmă printr-un nou apel API numele și tipurile salvate."""
    active_properties = client.send(ListItemProperties())
    check_property_types(active_properties, require_all=True)
    print(f"Confirmat prin API: toate cele {len(PROPRIETATI_CATALOG)} proprietăți au tipurile corecte.")
    return active_properties


def get_config():
    load_dotenv(ROOT / ".env", override=False)
    values = {}
    for name in ("RECOMBEE_DATABASE_ID", "RECOMBEE_PRIVATE_TOKEN", "RECOMBEE_REGION"):
        value = os.getenv(name, "").strip()
        if not value or value.startswith("completeaza_"):
            raise ValueError(f"Completează {name} în .env (model: .env.example).")
        values[name] = value
    if values["RECOMBEE_REGION"] not in REGIONS:
        raise ValueError("Regiune invalidă. Copiază regiunea bazei din Recombee Admin UI.")
    return values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=PATH_DATASET, help="Calea CSV-ului")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Verificare locală, fără API sau token")
    mode.add_argument("--verify-only", action="store_true", help="Doar verifică schema prin API")
    args = parser.parse_args(argv)
    try:
        df = load_dataset(args.dataset)
        print("\nSchema transmisă către Recombee:")
        for prop in PROPRIETATI_CATALOG:
            print(f"- {prop['name']}: {prop['type']}")
        if args.dry_run:
            print("\nDRY RUN: validare locală încheiată; nu s-a apelat Recombee.")
            return 0
        config = get_config()
        client = RecombeeClient(
            config["RECOMBEE_DATABASE_ID"],
            config["RECOMBEE_PRIVATE_TOKEN"],
            region=REGIONS[config["RECOMBEE_REGION"]],
        )
        if not args.verify_only:
            set_properties(client)
        active_properties = verify(client)
        # Raportul se scrie numai după confirmarea schemei de către server.
        report_path = ROOT / "reports" / "recombee_properties.json"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps({
            "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            "database_id": config["RECOMBEE_DATABASE_ID"],
            "region": config["RECOMBEE_REGION"],
            "dataset_rows": len(df),
            "properties": active_properties,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Raport de verificare: {report_path.relative_to(ROOT)}")
        return 0
    except APIException as error:
        # Nu afișăm excepția completă: aceasta poate include URL-uri semnate.
        status = getattr(error, "status_code", "necunoscut")
        print(f"Eroare Recombee (HTTP {status}). Verifică Database ID, private token, "
              "regiunea și permisiunile. Poți relua comanda după corectare.", file=sys.stderr)
    except RequestException:
        print("Conexiunea la Recombee a eșuat. Verifică rețeaua și reîncearcă.", file=sys.stderr)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        print(f"Eroare: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

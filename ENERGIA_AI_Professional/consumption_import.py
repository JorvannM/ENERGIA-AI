"""Importation securisee des consommations CSV et Excel."""

import csv
import io
import math
from pathlib import Path

REQUIRED_COLUMNS = {"year", "month", "energy", "kwh"}
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_RECORDS = 12000


def _validate_records(rows):
    records = []

    for index, row in enumerate(rows, start=2):
        if not any(value is not None and str(value).strip()
                   for value in row.values()):
            continue

        try:
            year = int(row["year"])
            month = int(row["month"])
            energy = str(row["energy"]).strip().lower()
            kwh = float(str(row["kwh"]).replace(",", "."))
            raw_cost = row.get("cost_eur")
            cost = (
                0.0 if raw_cost is None or str(raw_cost).strip() == ""
                else float(str(raw_cost).replace(",", "."))
            )
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(
                f"Ligne {index} : donnees invalides."
            ) from exc

        if not 1900 <= year <= 2100:
            raise ValueError(f"Ligne {index} : annee invalide.")

        if not 1 <= month <= 12:
            raise ValueError(f"Ligne {index} : mois invalide.")

        if not energy:
            raise ValueError(f"Ligne {index} : energie manquante.")

        if not math.isfinite(kwh) or not math.isfinite(cost):
            raise ValueError(f"Ligne {index} : valeur non finie.")

        if kwh < 0 or cost < 0:
            raise ValueError(f"Ligne {index} : valeur negative.")

        records.append({
            "year": year,
            "month": month,
            "energy": energy,
            "kwh": kwh,
            "cost_eur": cost
        })

        if len(records) > MAX_RECORDS:
            raise ValueError("Trop de lignes dans le fichier.")

    if not records:
        raise ValueError("Aucune consommation exploitable.")

    return records


def import_consumption_file(filename, content):
    """Retourne les consommations normalisees depuis CSV/XLSX."""

    if len(content) > MAX_FILE_BYTES:
        raise ValueError("Fichier trop volumineux (maximum 5 Mo).")

    extension = Path(filename).suffix.lower()

    if extension == ".csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "Le CSV doit etre encode en UTF-8."
            ) from exc

        sample = text[:4096]

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.DictReader(
            io.StringIO(text), delimiter=delimiter
        )

        columns = set(reader.fieldnames or [])

        if not REQUIRED_COLUMNS.issubset(columns):
            raise ValueError(
                "Colonnes requises : year, month, energy, kwh."
            )

        return _validate_records(reader)

    if extension == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise RuntimeError(
                "Installer openpyxl : py -m pip install openpyxl"
            ) from exc

        workbook = load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=True
        )

        try:
            sheet = workbook.active
            rows = sheet.iter_rows(values_only=True)

            headers = next(rows, None)

            if not headers:
                raise ValueError("Fichier Excel vide.")

            columns = [
                str(value).strip() if value is not None else ""
                for value in headers
            ]

            if not REQUIRED_COLUMNS.issubset(set(columns)):
                raise ValueError(
                    "Colonnes requises : year, month, energy, kwh."
                )

            def dictionaries():
                for values in rows:
                    yield dict(zip(columns, values))

            return _validate_records(dictionaries())

        finally:
            workbook.close()

    raise ValueError(
        "Format non pris en charge. Utiliser CSV ou XLSX."
    )

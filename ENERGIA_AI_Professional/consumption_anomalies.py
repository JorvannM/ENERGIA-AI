"""Detection explicable des anomalies de consommation."""

from collections import defaultdict
from statistics import median
import math


def detect_consumption_anomalies(records):
    """
    Analyse mensuelle par energie.

    Detecte :
    - pics inhabituels
    - baisses inhabituelles
    - variations brutales
    - mois manquants

    Les seuils sont indicatifs.
    """

    if not records:
        return {
            "available": False,
            "anomalies": [],
            "anomaly_count": 0,
            "message": "Aucune donnee disponible."
        }

    grouped = defaultdict(lambda: defaultdict(float))

    for record in records:
        year = int(record["year"])
        month = int(record["month"])
        energy = str(record["energy"]).strip().lower()
        kwh = float(record["kwh"])

        if not 1900 <= year <= 2100:
            raise ValueError("Annee invalide.")

        if not 1 <= month <= 12:
            raise ValueError("Mois invalide.")

        if not energy:
            raise ValueError("Energie manquante.")

        if not math.isfinite(kwh) or kwh < 0:
            raise ValueError("Consommation invalide.")

        grouped[energy][(year, month)] += kwh

    anomalies = []

    for energy, monthly in grouped.items():
        periods = sorted(monthly)

        values = [monthly[p] for p in periods]

        reference = median(values)

        # Detection des valeurs atypiques.
        # Au moins 6 mois sont requis.
        if len(values) >= 6 and reference > 0:

            for period in periods:
                value = monthly[period]
                ratio = value / reference

                if ratio >= 1.5:
                    anomalies.append({
                        "type": "high_consumption",
                        "severity": "warning",
                        "energy": energy,
                        "year": period[0],
                        "month": period[1],
                        "kwh": round(value, 2),
                        "reference_kwh": round(reference, 2),
                        "message": (
                            "Consommation superieure "
                            "de 50 % ou plus a la mediane."
                        )
                    })

                elif ratio <= 0.5:
                    anomalies.append({
                        "type": "low_consumption",
                        "severity": "info",
                        "energy": energy,
                        "year": period[0],
                        "month": period[1],
                        "kwh": round(value, 2),
                        "reference_kwh": round(reference, 2),
                        "message": (
                            "Consommation inferieure "
                            "de 50 % ou plus a la mediane."
                        )
                    })

        # Variations entre mois consecutifs uniquement.
        for previous, current in zip(periods, periods[1:]):

            previous_index = previous[0] * 12 + previous[1]
            current_index = current[0] * 12 + current[1]

            if current_index - previous_index != 1:
                continue

            old = monthly[previous]
            new = monthly[current]

            if old <= 0:
                continue

            variation = (new - old) / old * 100

            if abs(variation) >= 40:
                anomalies.append({
                    "type": "sudden_change",
                    "severity": "warning",
                    "energy": energy,
                    "year": current[0],
                    "month": current[1],
                    "kwh": round(new, 2),
                    "variation_pct": round(variation, 1),
                    "message": (
                        "Variation mensuelle importante "
                        "a examiner."
                    )
                })

        # Detection des mois absents dans la periode.
        if len(periods) >= 2:
            first = periods[0][0] * 12 + periods[0][1] - 1
            last = periods[-1][0] * 12 + periods[-1][1] - 1

            known = {
                year * 12 + month - 1
                for year, month in periods
            }

            for index in range(first, last + 1):
                if index not in known:
                    year, month_index = divmod(index, 12)

                    anomalies.append({
                        "type": "missing_data",
                        "severity": "info",
                        "energy": energy,
                        "year": year,
                        "month": month_index + 1,
                        "message": (
                            "Aucun releve disponible "
                            "pour cette periode."
                        )
                    })

    anomalies.sort(
        key=lambda item: (
            item["year"],
            item["month"],
            item["energy"],
            item["type"]
        )
    )

    return {
        "available": True,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "method": "Regles statistiques explicables",
        "limitations": (
            "Analyse indicative sans correction meteo, "
            "occupation ou saisonnalite. "
            "Une anomalie ne prouve pas un defaut technique."
        )
    }

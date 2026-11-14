"""Analyse des consommations energetiques mensuelles."""

from collections import defaultdict
from statistics import mean


def analyze_monthly_consumption(records):
    """
    records: liste de dictionnaires :
    {
        "year": 2026,
        "month": 1,
        "energy": "electricity",
        "kwh": 1500,
        "cost_eur": 300
    }
    """

    if not records:
        return {
            "available": False,
            "message": "Aucune donnee de consommation."
        }

    monthly = defaultdict(lambda: {
        "kwh": 0.0,
        "cost_eur": 0.0
    })

    by_energy = defaultdict(float)

    for record in records:
        year = int(record["year"])
        month = int(record["month"])
        energy = str(record["energy"]).strip().lower()
        kwh = float(record["kwh"])
        cost = float(record.get("cost_eur", 0) or 0)

        if not 1 <= month <= 12:
            raise ValueError("Mois invalide.")

        if not energy:
            raise ValueError("Type d'energie manquant.")

        if kwh < 0 or cost < 0:
            raise ValueError("Valeurs negatives interdites.")

        key = (year, month)
        monthly[key]["kwh"] += kwh
        monthly[key]["cost_eur"] += cost
        by_energy[energy] += kwh

    periods = [
        {
            "year": year,
            "month": month,
            "kwh": round(values["kwh"], 2),
            "cost_eur": round(values["cost_eur"], 2)
        }
        for (year, month), values in sorted(monthly.items())
    ]

    total_kwh = sum(p["kwh"] for p in periods)
    total_cost = sum(p["cost_eur"] for p in periods)

    peak = max(periods, key=lambda p: p["kwh"])

    return {
        "available": True,
        "period_count": len(periods),
        "total_kwh": round(total_kwh, 2),
        "total_cost_eur": round(total_cost, 2),
        "average_monthly_kwh": round(
            mean(p["kwh"] for p in periods), 2
        ),
        "peak_month": peak,
        "by_energy": dict(by_energy),
        "monthly": periods
    }

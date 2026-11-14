"""Comparaison annuelle des consommations energetiques."""

from collections import defaultdict
import math


def compare_annual_consumption(records):
    """Comparer les annees par energie, avec controle de couverture."""

    grouped = defaultdict(
        lambda: {
            "months": set(),
            "kwh": 0.0,
            "cost_eur": 0.0,
            "cost_complete": True
        }
    )

    for record in records:
        year = int(record["year"])
        month = int(record["month"])
        energy = str(record["energy"]).strip().lower()
        kwh = float(record["kwh"])

        raw_cost = record.get("cost_eur")
        has_cost = raw_cost is not None and str(raw_cost).strip() != ""
        cost = float(raw_cost) if has_cost else 0.0

        if not 1900 <= year <= 2100 or not 1 <= month <= 12:
            raise ValueError("Periode invalide.")

        if not energy or not all(
            math.isfinite(v) and v >= 0 for v in (kwh, cost)
        ):
            raise ValueError("Donnees de consommation invalides.")

        entry = grouped[(energy, year)]
        entry["months"].add(month)
        entry["kwh"] += kwh
        entry["cost_eur"] += cost
        entry["cost_complete"] &= has_cost

    annual = []

    for (energy, year), data in sorted(grouped.items()):
        annual.append({
            "energy": energy,
            "year": year,
            "months_count": len(data["months"]),
            "complete_year": len(data["months"]) == 12,
            "total_kwh": round(data["kwh"], 2),
            "total_cost_eur": (
                round(data["cost_eur"], 2)
                if data["cost_complete"] else None
            )
        })

    comparisons = []

    by_key = {
        (item["energy"], item["year"]): item
        for item in annual
    }

    for current in annual:
        previous = by_key.get(
            (current["energy"], current["year"] - 1)
        )

        if previous is None:
            continue

        comparable = (
            current["complete_year"]
            and previous["complete_year"]
        )

        old = previous["total_kwh"]
        new = current["total_kwh"]

        variation_pct = (
            round((new - old) / old * 100, 2)
            if comparable and old > 0 else None
        )

        comparisons.append({
            "energy": current["energy"],
            "previous_year": previous["year"],
            "current_year": current["year"],
            "comparable": comparable,
            "variation_kwh": (
                round(new - old, 2) if comparable else None
            ),
            "variation_pct": variation_pct,
            "previous_kwh": old,
            "current_kwh": new,
            "note": (
                "Comparaison annuelle complete."
                if comparable else
                "Comparaison non fiable : annees incompletes."
            )
        })

    return {
        "available": bool(annual),
        "annual": annual,
        "comparisons": comparisons,
        "method": "Comparaison annuelle par energie",
        "limitations": (
            "Comparaison brute sans correction climatique "
            "ni ajustement de l'occupation."
        )
    }

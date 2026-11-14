"""Analyse croisee du diagnostic et des consommations."""

import math


def _valid_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and number >= 0 else None
    except (TypeError, ValueError):
        return None


def analyze_combined_energy(building_result, consumption_report):
    """Croiser deux sources sans attribuer de causes non demontrees."""

    if not isinstance(building_result, dict):
        building_result = {}

    if not isinstance(consumption_report, dict):
        consumption_report = {}

    diagnostic = building_result.get("data") or {}
    analysis = consumption_report.get("analysis") or {}
    comparison = consumption_report.get("comparison") or {}
    anomalies = consumption_report.get("anomalies") or {}

    estimated = _valid_number(diagnostic.get("total_kwh"))
    measured = _valid_number(analysis.get("total_kwh"))

    observations = []
    limitations = []

    if estimated is None:
        limitations.append(
            "Consommation estimee du diagnostic indisponible."
        )

    if measured is None:
        limitations.append(
            "Consommation mesuree indisponible."
        )

    # Le total importe peut couvrir plusieurs annees.
    # Ne jamais le comparer directement a une estimation annuelle.
    annual = comparison.get("annual") or []

    complete = [
        item for item in annual
        if item.get("complete_year")
        and _valid_number(item.get("total_kwh")) is not None
    ]

    years = sorted({
        item["year"] for item in complete
    })

    measured_year = None
    measured_annual = None

    if len(years) == 1:
        year = years[0]

        all_year_records = [
            item for item in annual
            if item.get("year") == year
        ]

        if all(
            item.get("complete_year")
            for item in all_year_records
        ):
            measured_year = year
            measured_annual = sum(
                float(item["total_kwh"])
                for item in all_year_records
            )

    if measured_year is None:
        limitations.append(
            "Aucune annee unique et complete ne peut etre "
            "retenue automatiquement pour une comparaison."
        )

    gap_kwh = None
    gap_pct = None

    if estimated is not None and measured_annual is not None:
        if estimated > 0:
            gap_kwh = measured_annual - estimated
            gap_pct = gap_kwh / estimated * 100

            observations.append({
                "category": "energy_gap",
                "priority": (
                    "warning" if abs(gap_pct) >= 15 else "info"
                ),
                "title": "Ecart entre estimation et mesure",
                "message": (
                    f"Ecart indicatif : {gap_pct:+.1f} %. "
                    "Verifier que le perimetre energetique, "
                    "les usages et les periodes sont identiques."
                )
            })
        else:
            limitations.append(
                "Estimation nulle : pourcentage non calculable."
            )

    anomaly_count = anomalies.get("anomaly_count", 0)

    if anomaly_count:
        observations.append({
            "category": "anomalies",
            "priority": "warning",
            "title": "Variations inhabituelles",
            "message": (
                f"{anomaly_count} signalement(s) detecte(s). "
                "Verifier les releves, la meteo, les horaires "
                "et les conditions d'exploitation."
            )
        })

    for item in comparison.get("comparisons", []):
        variation = item.get("variation_pct")

        if not item.get("comparable") or variation is None:
            continue

        observations.append({
            "category": "annual_change",
            "priority": "info",
            "title": "Evolution : " + str(item["energy"]),
            "message": (
                f"Variation de {variation:+.1f} % entre "
                f"{item['previous_year']} et "
                f"{item['current_year']}. "
                "Cause non determinee."
            )
        })

    limitations.append(
        "Comparaison indicative non normalisee selon la meteo, "
        "l'occupation ou les changements d'equipements."
    )

    return {
        "available": bool(observations),
        "estimated_annual_kwh": estimated,
        "measured_total_imported_kwh": measured,
        "measured_year": measured_year,
        "measured_annual_kwh": measured_annual,
        "gap_kwh": gap_kwh,
        "gap_pct": gap_pct,
        "observations": observations,
        "limitations": limitations,
        "method": "Croisement deterministe de donnees calculees et mesurees",
    }

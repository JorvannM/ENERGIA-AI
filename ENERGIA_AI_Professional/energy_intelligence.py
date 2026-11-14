
"""Analyse intelligente et prudente du bilan energetique."""

import math


def analyze_energy_breakdown(breakdown: dict) -> dict:
    """Identifie les principaux postes et les limites des donnees."""

    observations = []
    by_use = breakdown.get("by_use", {})
    by_energy = breakdown.get("by_energy", {})

    quantified = []

    for key, item in by_use.items():
        value = item.get("kwh_year")

        if value is None:
            continue

        value = float(value)

        if not math.isfinite(value) or value < 0:
            continue

        quantified.append({
            "key": key,
            "label": item.get("label", key),
            "kwh_year": value,
            "source": item.get("source", "unknown"),
        })

    quantified.sort(
        key=lambda item: item["kwh_year"],
        reverse=True
    )

    if quantified:
        leader = quantified[0]

        observations.append({
            "type": "dominant_use",
            "severity": "information",
            "title": "Poste énergétique le plus consommateur parmi les postes quantifiés",
            "detail": (
                f"{leader['label']} : "
                f"{leader['kwh_year']:.0f} kWh/an "
                f"({leader['source']})."
            ),
            "confidence": (
                "indicative" if leader["source"] == "theoretical"
                else "declared"
            ),
        })

    missing = [
        item.get("label", key)
        for key, item in by_use.items()
        if item.get("kwh_year") is None
    ]

    if missing:
        observations.append({
            "type": "missing_data",
            "severity": "information",
            "title": "Postes non quantifiés",
            "detail": ", ".join(missing),
            "confidence": "high",
        })

    total = float(breakdown.get("total_kwh_year", 0) or 0)

    if total > 0:
        energies = sorted(
            (
                {
                    "key": key,
                    "label": item.get("label", key),
                    "kwh_year": float(item.get("kwh_year", 0) or 0),
                }
                for key, item in by_energy.items()
            ),
            key=lambda item: item["kwh_year"],
            reverse=True,
        )

        if energies:
            dominant = energies[0]
            share = dominant["kwh_year"] / total * 100

            observations.append({
                "type": "dominant_energy",
                "severity": "information",
                "title": "Énergie dominante",
                "detail": (
                    f"{dominant['label']} : "
                    f"{share:.1f} % de la consommation annualisée."
                ),
                "confidence": "declared",
            })


    # Controle indicatif des estimations electriques.
    # Ne pas inclure le chauffage : son vecteur n'est pas
    # garanti par les seules donnees du bilan.

    electric_uses = ("cooling", "ventilation", "lighting")

    estimated_electric = [
        by_use[key]["kwh_year"]
        for key in electric_uses
        if (
            key in by_use
            and by_use[key].get("source") == "theoretical"
            and by_use[key].get("kwh_year") is not None
        )
    ]

    declared_electric = float(
        by_energy.get("electricity", {}).get("kwh_year", 0) or 0
    )

    if estimated_electric and declared_electric > 0:
        estimated_total = sum(float(v) for v in estimated_electric)
        ratio = estimated_total / declared_electric

        if ratio > 1.10:
            observations.append({
                "type": "electricity_inconsistency",
                "severity": "warning",
                "title": "Écart entre estimations et consommation électrique",
                "detail": (
                    f"Équipements estimés : {estimated_total:.0f} kWh/an ; "
                    f"électricité déclarée : {declared_electric:.0f} kWh/an. "
                    "Vérifier les hypothèses et le périmètre des données."
                ),
                "confidence": "indicative",
            })

    theoretical_count = sum(
        item["source"] == "theoretical"
        for item in quantified
    )

    declared_count = sum(
        item["source"] in ("declared", "declared_annualized")
        for item in quantified
    )

    missing_count = len(missing)

    if missing_count:
        quality = "incomplete"
    elif theoretical_count:
        quality = "estimated"
    elif declared_count:
        quality = "declared"
    else:
        quality = "unavailable"

    return {
        "observations": observations,
        "ranked_uses": quantified,
        "data_quality": {
            "status": quality,
            "quantified_uses": len(quantified),
            "theoretical_uses": theoretical_count,
            "declared_uses": declared_count,
            "missing_uses": missing_count,
            "fully_measured": False,
        },
        "methodology": (
            "Classement indicatif des postes quantifies. "
            "Les estimations theoriques et les consommations "
            "declarees ne constituent pas un bilan mesure "
            "et ne sont pas additionnees au total par energie."
        ),
    }

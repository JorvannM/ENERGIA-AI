"""Simulation indicative des economies electriques de climatisation."""
import math


def simulate_cooling_savings(data: dict) -> dict:
    keys = (
        "cooling_capacity_kw",
        "cooling_hours_year",
        "cooling_eer_existing",
        "cooling_eer_proposed",
    )

    if any(data.get(key) is None for key in keys):
        return {
            "available": False,
            "reason": "Donnees insuffisantes pour simuler la climatisation."
        }

    try:
        capacity, hours, eer_before, eer_after = (
            float(data[key]) for key in keys
        )

        if not all(math.isfinite(v) for v in (
            capacity, hours, eer_before, eer_after
        )):
            raise ValueError("Valeurs non finies.")

        if capacity <= 0 or eer_before <= 0 or eer_after <= 0:
            raise ValueError("Puissance ou EER invalide.")

        if not 0 <= hours <= 8760:
            raise ValueError("Duree annuelle invalide.")

        before = capacity * hours / eer_before
        after = capacity * hours / eer_after
        savings = before - after

        return {
            "available": True,
            "before_kwh_year": round(before, 2),
            "after_kwh_year": round(after, 2),
            "savings_kwh_year": round(savings, 2),
            "savings_pct": round(100 * savings / before, 2) if before > 0 else None,
            "assumption": (
                "Besoin frigorifique identique avant et apres. "
                "Puissance frigorifique constante pendant les heures saisies. "
                "EER supposes representatifs du fonctionnement. "
                "Simulation indicative, non reglementaire."
            )
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres de climatisation invalides."
        }

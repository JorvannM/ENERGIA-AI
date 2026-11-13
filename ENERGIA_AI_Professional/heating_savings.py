"""Simulation indicative des economies d'energie de chauffage."""
import math


def simulate_heating_savings(data: dict) -> dict:
    consumption = data.get("heating_energy_kwh_year")
    reduction = data.get("heating_reduction_pct")

    if consumption is None or reduction is None:
        return {
            "available": False,
            "reason": "Donnees insuffisantes pour simuler le chauffage."
        }

    try:
        consumption = float(consumption)
        reduction = float(reduction)

        if not all(math.isfinite(v) for v in (consumption, reduction)):
            raise ValueError("Valeurs non finies.")

        if consumption < 0 or not 0 <= reduction <= 100:
            raise ValueError("Valeurs hors limites.")

        savings = consumption * reduction / 100
        after = consumption - savings

        return {
            "available": True,
            "before_kwh_year": round(consumption, 2),
            "after_kwh_year": round(after, 2),
            "savings_kwh_year": round(savings, 2),
            "savings_pct": round(reduction, 2),
            "assumption": (
                "Reduction saisie par l'utilisateur. "
                "Simulation indicative, sans calcul thermique detaille. "
                "Le pourcentage doit etre justifie par une etude technique."
            )
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres de chauffage invalides."
        }

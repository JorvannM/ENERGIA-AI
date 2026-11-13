"""Simulation indicative des economies electriques de ventilation."""
import math


def simulate_ventilation_savings(data: dict) -> dict:
    keys = (
        "ventilation_fan_power_w",
        "ventilation_schedule_hours_day",
        "ventilation_proposed_hours_day",
        "occupancy_days_year",
    )

    if any(data.get(key) is None for key in keys):
        return {
            "available": False,
            "reason": "Donnees insuffisantes pour simuler la ventilation."
        }

    try:
        power = float(data["ventilation_fan_power_w"])
        before_hours = float(data["ventilation_schedule_hours_day"])
        after_hours = float(data["ventilation_proposed_hours_day"])
        days = float(data["occupancy_days_year"])

        values = (power, before_hours, after_hours, days)

        if not all(math.isfinite(v) for v in values):
            raise ValueError("Valeur non finie")

        if power <= 0 or days <= 0 or days > 366:
            raise ValueError("Puissance ou jours invalides")

        if not (0 <= before_hours <= 24 and 0 <= after_hours <= 24):
            raise ValueError("Horaires invalides")

        before = power * before_hours * days / 1000
        after = power * after_hours * days / 1000
        savings = before - after

        return {
            "available": True,
            "before_kwh_year": round(before, 2),
            "after_kwh_year": round(after, 2),
            "savings_kwh_year": round(savings, 2),
            "savings_pct": round(100 * savings / before, 2) if before > 0 else None,
            "assumption": (
                "Puissance electrique constante. "
                "Jours de fonctionnement supposes egaux aux jours d'occupation. "
                "Horaires proposes a valider selon les besoins de qualite d'air."
            )
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres de ventilation invalides."
        }

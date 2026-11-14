"""Calcul economique des simulations techniques."""

import math


def evaluate_equipment_economics(
    simulation: dict,
    energy_price_eur_kwh=None,
    investment_eur=None
) -> dict:
    if not simulation.get("available"):
        return {
            "available": False,
            "reason": "Simulation technique indisponible."
        }

    savings = simulation.get("savings_kwh_year")

    if not isinstance(savings, (int, float)):
        return {
            "available": False,
            "reason": "Economie energetique non quantifiee."
        }

    if not math.isfinite(savings) or savings <= 0:
        return {
            "available": False,
            "reason": "Economie energetique non positive."
        }

    if energy_price_eur_kwh is None:
        return {
            "available": False,
            "reason": "Tarif energetique non renseigne."
        }

    try:
        price = float(energy_price_eur_kwh)

        if not math.isfinite(price) or price < 0:
            raise ValueError("Tarif invalide")

        annual_savings = savings * price
        investment = None
        payback = None

        if investment_eur is not None:
            investment = float(investment_eur)

            if not math.isfinite(investment) or investment < 0:
                raise ValueError("Investissement invalide")

            if annual_savings > 0:
                payback = investment / annual_savings

        return {
            "available": True,
            "annual_savings_eur": round(annual_savings, 2),
            "investment_eur": investment,
            "payback_years": (
                round(payback, 2)
                if payback is not None
                else None
            ),
            "energy_savings_kwh_year": savings,
            "note": (
                "Temps de retour simple indicatif, "
                "hors actualisation, maintenance "
                "et evolution des tarifs."
            )
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres economiques invalides."
        }


def resolve_heating_energy_price(data: dict):
    """Select a heating tariff without guessing the energy source.

    Assumes heating_energy_kwh_year represents billed final energy.
    """
    explicit = data.get("heating_energy_price_eur_kwh")
    if explicit is not None:
        return explicit

    kind = str(data.get("heating_type") or "unknown").strip().lower()

    if kind in ("electric", "electricity", "electrique", "?lectrique", "heat_pump"):
        return data.get("electricity_price_eur_kwh")

    if kind in ("gas", "gaz", "chaudiere gaz", "chaudi?re gaz"):
        return data.get("gas_price_eur_kwh")

    if kind in ("district", "district_heating", "reseau de chaleur", "r?seau de chaleur"):
        return data.get("district_price_eur_kwh")

    return None

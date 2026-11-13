import math

from lighting_savings import simulate_led_savings


def simulate_led_economics(data: dict) -> dict:
    energy = simulate_led_savings(data)

    if not energy["available"]:
        return {
            "available": False,
            "reason": energy["reason"]
        }

    price = data.get("electricity_price_eur_kwh")
    investment = data.get("lighting_investment_eur")

    if price is None:
        return {
            "available": False,
            "reason": "Prix de l'electricite non renseigne."
        }

    try:
        price = float(price)

        if not math.isfinite(price) or price < 0:
            raise ValueError("Prix invalide")

        annual_savings = energy["savings_kwh_year"] * price

        payback = None
        investment_value = None

        if investment is not None:
            investment_value = float(investment)

            if not math.isfinite(investment_value) or investment_value < 0:
                raise ValueError("Investissement invalide")

            if annual_savings > 0:
                payback = investment_value / annual_savings

        return {
            "available": True,
            "annual_savings_eur": round(annual_savings, 2),
            "investment_eur": investment_value,
            "payback_years": round(payback, 2) if payback is not None else None,
            "energy_savings_kwh_year": energy["savings_kwh_year"],
            "note": (
                "Estimation indicative. Temps de retour simple "
                "hors actualisation, maintenance et evolution des tarifs."
            )
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres economiques invalides."
        }

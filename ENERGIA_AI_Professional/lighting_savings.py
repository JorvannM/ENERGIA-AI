def simulate_led_savings(data: dict) -> dict:
    keys = (
        "lighting_fixture_count",
        "lighting_power_existing_w",
        "lighting_power_proposed_w",
        "lighting_schedule_hours_day",
        "occupancy_days_year",
    )

    if any(data.get(key) is None for key in keys):
        return {
            "available": False,
            "reason": "Donnees insuffisantes pour simuler les economies LED."
        }

    try:
        import math

        n = float(data["lighting_fixture_count"])
        p_before = float(data["lighting_power_existing_w"])
        p_after = float(data["lighting_power_proposed_w"])
        hours_day = float(data["lighting_schedule_hours_day"])
        days_year = float(data["occupancy_days_year"])

        values = (n, p_before, p_after, hours_day, days_year)

        if not all(math.isfinite(v) and v > 0 for v in values):
            raise ValueError("Parametres non valides")

        if not n.is_integer() or hours_day > 24 or days_year > 366:
            raise ValueError("Parametres incoherents")

        hours_year = hours_day * days_year
        before = n * p_before * hours_year / 1000
        after = n * p_after * hours_year / 1000
        savings = before - after

        return {
            "available": True,
            "before_kwh_year": round(before, 2),
            "after_kwh_year": round(after, 2),
            "savings_kwh_year": round(savings, 2),
            "savings_pct": round(100 * savings / before, 2),
            "assumption": "Heures annuelles = heures par jour x jours d'occupation."
        }

    except (TypeError, ValueError, OverflowError):
        return {
            "available": False,
            "reason": "Parametres LED invalides ou incoherents."
        }

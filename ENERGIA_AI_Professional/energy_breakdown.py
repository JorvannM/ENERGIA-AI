"""Bilan energetique par energie et par usage, sans double comptage."""

import math


def build_energy_breakdown(data: dict) -> dict:
    """Construit un bilan indicatif a partir des donnees disponibles."""

    energy_keys = {
        "electricity": "Electricite",
        "gas": "Gaz",
        "district": "Reseau de chaleur",
        "other": "Autres energies",
    }

    period = float(data.get("data_period_months", 12) or 12)
    if not math.isfinite(period) or period <= 0:
        raise ValueError("Periode de consommation invalide.")

    factor = 12.0 / period
    by_energy = {}

    for key, label in energy_keys.items():
        value = float(data.get(f"{key}_kwh", 0) or 0)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Consommation invalide : {key}")
        by_energy[key] = {
            "label": label,
            "kwh_year": round(value * factor, 2),
            "source": "declared_annualized",
        }

    total = round(sum(x["kwh_year"] for x in by_energy.values()), 2)

    uses = {
        "heating": {
            "label": "Chauffage",
            "kwh_year": None,
            "source": "not_quantified",
        },
        "cooling": {
            "label": "Climatisation",
            "kwh_year": None,
            "source": "not_quantified",
        },
        "ventilation": {
            "label": "Ventilation",
            "kwh_year": None,
            "source": "not_quantified",
        },
        "lighting": {
            "label": "Eclairage",
            "kwh_year": None,
            "source": "not_quantified",
        },
        "other_uses": {
            "label": "Autres usages",
            "kwh_year": None,
            "source": "not_quantified",
        },
    }


    # Consommation de chauffage declaree
    heating = data.get("heating_energy_kwh_year")
    if heating is not None:
        value = float(heating)
        if math.isfinite(value) and value >= 0:
            uses["heating"]["kwh_year"] = round(value, 2)
            uses["heating"]["source"] = "declared"

    # Consommation electrique theorique de climatisation
    cooling_keys = (
        "cooling_capacity_kw",
        "cooling_hours_year",
        "cooling_eer_existing",
    )
    if all(data.get(k) is not None for k in cooling_keys):
        capacity, hours, eer = (
            float(data[k]) for k in cooling_keys
        )
        if (
            all(math.isfinite(v) for v in (capacity, hours, eer))
            and capacity > 0
            and 0 <= hours <= 8760
            and eer > 0
        ):
            uses["cooling"]["kwh_year"] = round(
                capacity * hours / eer, 2
            )
            uses["cooling"]["source"] = "theoretical"

    # Consommation electrique theorique de ventilation
    power = data.get("ventilation_fan_power_w")
    hours_day = data.get("ventilation_schedule_hours_day")
    days = data.get("occupancy_days_year", 250)
    if power is not None and hours_day is not None:
        values = (float(power), float(hours_day), float(days))
        if (
            all(math.isfinite(v) for v in values)
            and values[0] > 0
            and 0 <= values[1] <= 24
            and 0 <= values[2] <= 366
        ):
            uses["ventilation"]["kwh_year"] = round(
                values[0] * values[1] * values[2] / 1000, 2
            )
            uses["ventilation"]["source"] = "theoretical"

    # Consommation electrique theorique d'eclairage
    count = data.get("lighting_fixture_count")
    power = data.get("lighting_power_existing_w")
    hours_day = data.get("lighting_schedule_hours_day")
    if all(v is not None for v in (count, power, hours_day)):
        values = (float(count), float(power), float(hours_day), float(days))
        if (
            all(math.isfinite(v) for v in values)
            and values[0] > 0
            and values[1] > 0
            and 0 <= values[2] <= 24
            and 0 <= values[3] <= 366
        ):
            uses["lighting"]["kwh_year"] = round(
                values[0] * values[1] * values[2] * values[3] / 1000, 2
            )
            uses["lighting"]["source"] = "theoretical"

    return {
        "total_kwh_year": total,
        "by_energy": by_energy,
        "by_use": uses,
        "unallocated_kwh_year": None,
        "allocation_status": "not_available",
        "warning": (
            "Les consommations par usage ne sont pas deduites "
            "automatiquement des consommations par energie. "
            "Des mesures ou des hypotheses documentees sont necessaires."
        ),
    }

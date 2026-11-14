
"""Disponibilite des simulations energetiques V8."""

from lighting_savings import simulate_led_savings
from heating_savings import simulate_heating_savings
from cooling_savings import simulate_cooling_savings
from ventilation_savings import simulate_ventilation_savings


SIMULATORS = {
    "lighting": {
        "label": "Eclairage LED",
        "function": simulate_led_savings,
        "fields": {
            "lighting_fixture_count": "Nombre de luminaires",
            "lighting_power_existing_w": "Puissance actuelle (W)",
            "lighting_power_proposed_w": "Puissance LED proposee (W)",
            "lighting_schedule_hours_day": "Heures de fonctionnement par jour",
            "occupancy_days_year": "Jours de fonctionnement par an",
        },
    },
    "heating": {
        "label": "Chauffage",
        "function": simulate_heating_savings,
        "fields": {
            "heating_energy_kwh_year": "Consommation annuelle du chauffage (kWh)",
            "heating_reduction_pct": "Reduction envisagee et justifiee (%)",
        },
    },
    "cooling": {
        "label": "Climatisation",
        "function": simulate_cooling_savings,
        "fields": {
            "cooling_capacity_kw": "Puissance frigorifique (kW)",
            "cooling_hours_year": "Heures de fonctionnement annuelles",
            "cooling_eer_existing": "EER actuel",
            "cooling_eer_proposed": "EER propose",
        },
    },
    "ventilation": {
        "label": "Ventilation",
        "function": simulate_ventilation_savings,
        "fields": {
            "ventilation_fan_power_w": "Puissance des ventilateurs (W)",
            "ventilation_schedule_hours_day": "Heures actuelles par jour",
            "ventilation_proposed_hours_day": "Heures proposees par jour",
            "occupancy_days_year": "Jours de fonctionnement par an",
        },
    },
}


def inspect_simulations(data: dict) -> dict:
    results = {}

    for key, config in SIMULATORS.items():
        missing = [
            {"field": field, "label": label}
            for field, label in config["fields"].items()
            if data.get(field) is None
        ]

        simulation = config["function"](data)

        results[key] = {
            "label": config["label"],
            "available": simulation.get("available", False),
            "missing_fields": missing,
            "result": simulation,
            "reason": simulation.get("reason"),
        }

    return results

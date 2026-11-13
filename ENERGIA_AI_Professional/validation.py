"""Validation et contrôle de cohérence des données bâtiment."""
from __future__ import annotations
import math
from typing import Any

REQUIRED_NUMERIC = ("surface_m2", "occupancy_hours_week", "occupancy_days_year",
                    "data_period_months", "electricity_kwh", "gas_kwh",
                    "district_kwh", "other_kwh", "annual_energy_cost_eur")

def validate_building(data: dict[str, Any]) -> dict:
    errors, warnings = [], []
    for key in REQUIRED_NUMERIC:
        value = data.get(key, 0)
        try:
            numeric = float(value)
            if not math.isfinite(numeric):
                errors.append(f"{key} doit etre un nombre fini.")
            elif numeric < 0:
                errors.append(f"{key} ne peut pas être négatif.")
        except (TypeError, ValueError):
            errors.append(f"{key} doit être numérique.")
    try:
        surface = float(data.get("surface_m2") or 0)
    except (TypeError, ValueError):
        surface = None
    if surface is not None and surface <= 0:
        errors.append("La surface utile doit être strictement positive.")
    try:
        period = float(data.get("data_period_months") or 0)
    except (TypeError, ValueError):
        period = None
    if period is not None and period <= 0:
        errors.append("La période de données doit être supérieure à zéro.")
    if period is not None and period != 12:
        warnings.append("La période n'est pas de 12 mois : annualiser avec prudence.")
    try:
        hours = float(data.get("occupancy_hours_week") or 0)
    except (TypeError, ValueError, OverflowError):
        hours = None
    if hours is not None and hours > 168:
        errors.append("Les heures d'occupation hebdomadaires dépassent 168 h.")
    try:
        days = float(data.get("occupancy_days_year") or 0)
    except (TypeError, ValueError, OverflowError):
        days = None
    if days is not None and days > 366:
        errors.append("Les jours d'occupation annuels dépassent 366.")
    energy_values = []
    for key in ("electricity_kwh", "gas_kwh", "district_kwh", "other_kwh"):
        try:
            value = float(data.get(key) or 0)
            if not math.isfinite(value):
                continue
            energy_values.append(value)
        except (TypeError, ValueError, OverflowError):
            continue

    energy = sum(energy_values)
    if energy == 0:
        warnings.append("Aucune consommation annuelle n'est renseignée.")
    if data.get("has_cooling") and data.get("cooling_type") in (None, "", "unknown"):
        warnings.append("Le refroidissement est déclaré présent, mais son système n'est pas caractérisé.")
    if data.get("has_ventilation") and data.get("ventilation_type") in (None, "", "unknown"):
        warnings.append("La ventilation est déclarée présente, mais son type est inconnu.")
    if not data.get("meter_separation"):
        warnings.append("Les usages ne sont pas tous sous-comptés : attribution par poste limitée.")
    led_fields = (
        "lighting_fixture_count",
        "lighting_power_existing_w",
        "lighting_power_proposed_w",
    )
    for key in led_fields:
        value = data.get(key)
        if value is None:
            continue
        try:
            number = float(value)
            if not math.isfinite(number) or number <= 0:
                errors.append(f"{key} doit etre strictement positif et fini.")
            elif key == "lighting_fixture_count" and not number.is_integer():
                errors.append(f"{key} doit etre un entier.")
        except (TypeError, ValueError, OverflowError):
            errors.append(f"{key} doit etre numerique.")

    economic_fields = (
        "electricity_price_eur_kwh",
        "lighting_investment_eur",
    )
    for key in economic_fields:
        value = data.get(key)
        if value is None:
            continue
        try:
            number = float(value)
            if not math.isfinite(number) or number < 0:
                errors.append(f"{key} doit etre positif ou nul et fini.")
        except (TypeError, ValueError, OverflowError):
            errors.append(f"{key} doit etre numerique.")

    return {"valid": not errors, "errors": errors, "warnings": warnings}

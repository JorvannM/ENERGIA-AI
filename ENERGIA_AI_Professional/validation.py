"""Validation et contrôle de cohérence des données bâtiment."""
from __future__ import annotations
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
            if numeric < 0:
                errors.append(f"{key} ne peut pas être négatif.")
        except (TypeError, ValueError):
            errors.append(f"{key} doit être numérique.")
    if float(data.get("surface_m2") or 0) <= 0:
        errors.append("La surface utile doit être strictement positive.")
    if int(data.get("data_period_months") or 0) <= 0:
        errors.append("La période de données doit être supérieure à zéro.")
    if int(data.get("data_period_months") or 0) != 12:
        warnings.append("La période n'est pas de 12 mois : annualiser avec prudence.")
    if float(data.get("occupancy_hours_week") or 0) > 168:
        errors.append("Les heures d'occupation hebdomadaires dépassent 168 h.")
    if float(data.get("occupancy_days_year") or 0) > 366:
        errors.append("Les jours d'occupation annuels dépassent 366.")
    energy = sum(float(data.get(k) or 0) for k in
                 ("electricity_kwh", "gas_kwh", "district_kwh", "other_kwh"))
    if energy == 0:
        warnings.append("Aucune consommation annuelle n'est renseignée.")
    if data.get("has_cooling") and data.get("cooling_type") in (None, "", "unknown"):
        warnings.append("Le refroidissement est déclaré présent, mais son système n'est pas caractérisé.")
    if data.get("has_ventilation") and data.get("ventilation_type") in (None, "", "unknown"):
        warnings.append("La ventilation est déclarée présente, mais son type est inconnu.")
    if not data.get("meter_separation"):
        warnings.append("Les usages ne sont pas tous sous-comptés : attribution par poste limitée.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}

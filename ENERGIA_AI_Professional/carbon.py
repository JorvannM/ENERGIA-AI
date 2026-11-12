"""Bilan carbone énergétique à partir de facteurs explicitement versionnés."""
import json
from pathlib import Path

def load_emission_factors(path=None):
    path = Path(path) if path else Path(__file__).parent / "data" / "emission_factors.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def estimate_carbon(data: dict, factors: dict | None = None) -> dict:
    factors = factors or load_emission_factors()
    by_energy = {}
    for energy, field in (("electricity", "electricity_kwh"), ("gas", "gas_kwh"),
                          ("district", "district_kwh"), ("other", "other_kwh")):
        factor = factors["factors_kgco2e_per_kwh"].get(energy)
        if factor is not None:
            by_energy[energy] = float(data.get(field, 0) or 0) * float(factor)
    total = sum(by_energy.values())
    return {"total_kgco2e": total, "total_tco2e": total / 1000,
            "by_energy_kgco2e": by_energy, "factor_metadata": factors.get("metadata", {}),
            "warning": "Estimation indicative. Vérifier année, périmètre et facteurs applicables."}

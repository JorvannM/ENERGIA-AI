"""Schémas de données du pré-diagnostic HVAC Building."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

ENERGIES = ("electricity", "gas", "district", "other")

@dataclass
class BuildingData:
    name: str = ""
    address: str = ""
    building_type: str = "bureaux"
    surface_m2: float = 500.0
    occupancy_hours_week: float = 50.0
    occupancy_days_year: int = 250
    construction_year: int | None = None
    climate_zone: str = "H1"
    heating_type: str = "unknown"
    cooling_type: str = "unknown"
    ventilation_type: str = "unknown"
    lighting_type: str = "unknown"
    dhw_type: str = "unknown"
    has_cooling: bool = True
    has_ventilation: bool = True
    has_lighting: bool = True
    has_dhw: bool = True
    meter_separation: bool = False
    data_period_months: int = 12
    electricity_kwh: float = 0.0
    gas_kwh: float = 0.0
    district_kwh: float = 0.0
    other_kwh: float = 0.0
    annual_energy_cost_eur: float = 0.0
    heating_setpoint_c: float | None = None
    cooling_setpoint_c: float | None = None
    ventilation_schedule_hours_day: float | None = None
    lighting_schedule_hours_day: float | None = None
    lighting_fixture_count: int | None = None
    lighting_power_existing_w: float | None = None
    lighting_power_proposed_w: float | None = None
    electricity_price_eur_kwh: float | None = None
    lighting_investment_eur: float | None = None
    dhw_gas_kwh: float | None = None
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "BuildingData":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in values.items() if k in allowed})

def normalize_building(data: BuildingData | dict) -> dict:
    return data.to_dict() if isinstance(data, BuildingData) else BuildingData.from_dict(data).to_dict()

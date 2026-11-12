"""Évaluation économique simple des scénarios d'économie."""
def estimate_economics(data: dict, savings: dict) -> dict:
    cost = float(data.get("annual_energy_cost_eur", 0) or 0)
    return {
        "annual_savings_eur_low": cost * float(savings.get("low_pct", 0)) / 100,
        "annual_savings_eur_high": cost * float(savings.get("high_pct", 0)) / 100,
        "investment_eur": None,
        "payback_years_low": None,
        "payback_years_high": None,
        "note": "Temps de retour non calculé faute de coûts d'investissement et de devis."
    }

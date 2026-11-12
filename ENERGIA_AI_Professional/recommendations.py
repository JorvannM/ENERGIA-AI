"""Génération de recommandations traçables, sans additionner des gains qui se recouvrent."""
def build_recommendations(diagnostics: dict, data: dict) -> list[dict]:
    output = []
    mapping = [
        ("heating", "Chauffage"), ("cooling", "Refroidissement"),
        ("ventilation", "Ventilation"), ("lighting", "Éclairage"),
        ("hot_water", "Eau chaude sanitaire"), ("operation", "Exploitation")
    ]
    for key, label in mapping:
        result = diagnostics.get(key, {})
        actions = result.get("actions", [])
        for action in actions:
            output.append({
                "title": action, "detail": action,
                "category": label, "priority": "À qualifier",
                "basis": "; ".join(result.get("alerts", [])) or "Piste de contrôle issue du module de diagnostic.",
                "savings_low_pct": 0, "savings_high_pct": 0,
                "checks": ["Visite technique", "Mesures ou historiques à confirmer"],
                "evidence": result.get("alerts", []),
                "savings_note": "Non chiffré faute de sous-comptage et de scénario quantifié."
            })
    return output

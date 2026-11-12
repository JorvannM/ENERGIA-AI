"""Diagnostic de l'eau chaude sanitaire (ECS)."""
def diagnose_hot_water(data: dict, rules: dict) -> dict:
    if not data.get("has_dhw", True):
        return {"alerts": [], "actions": ["Confirmer l'absence de besoin ECS."], "status": "absent"}
    alerts, actions = [], [
        "Vérifier les températures de stockage et de distribution selon les exigences sanitaires.",
        "Isoler les réseaux, limiter les bouclages inutiles et contrôler la programmation.",
        "Examiner les volumes de stockage et les pertes de maintien en température."
    ]
    if data.get("dhw_type", "unknown") in ("unknown", "", None):
        alerts.append("Production ECS non caractérisée.")
    if data.get("dhw_gas_kwh") is None and float(data.get("gas_kwh", 0) or 0) > 0:
        alerts.append("Le gaz est consommé mais la part ECS n'est pas isolée.")
    return {"alerts": alerts, "actions": actions, "status": "à investiguer"}

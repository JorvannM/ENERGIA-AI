"""Diagnostic de l'éclairage."""
def diagnose_lighting(data: dict, rules: dict) -> dict:
    if not data.get("has_lighting", True):
        return {"alerts": [], "actions": [], "status": "non applicable"}
    actions = ["Inventorier les puissances installées et les technologies de luminaires.",
               "Vérifier détection de présence, gradation et asservissement à la lumière naturelle."]
    alerts = []
    if data.get("lighting_type", "unknown") in ("unknown", "", None):
        alerts.append("Technologie d'éclairage non renseignée.")
    hours = data.get("lighting_schedule_hours_day")
    if hours is not None and float(hours) > 12:
        alerts.append("Durée d'éclairage déclarée supérieure à 12 h/j : vérifier les horaires.")
    return {"alerts": alerts, "actions": actions, "status": "à investiguer"}

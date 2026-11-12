"""Diagnostic du refroidissement."""
def diagnose_cooling(data: dict, rules: dict) -> dict:
    if not data.get("has_cooling", False):
        return {"alerts": [], "actions": ["Confirmer l'absence de refroidissement."], "status": "absent"}
    alerts, actions = [], []
    kind = data.get("cooling_type", "unknown")
    if kind in ("unknown", "", None):
        alerts.append("Type de production de froid non renseigné.")
    actions.extend([
        "Vérifier les horaires de marche et l'arrêt hors occupation.",
        "Contrôler les consignes, les filtres, les échangeurs et les températures de condensation.",
        "Rechercher les fonctionnements simultanés chauffage/refroidissement."
    ])
    setpoint = data.get("cooling_setpoint_c")
    if setpoint is not None and float(setpoint) < 24:
        alerts.append("Consigne de refroidissement inférieure à 24 °C : vérifier sa pertinence selon l'activité.")
    return {"alerts": alerts, "actions": actions, "status": "à investiguer"}

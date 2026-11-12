"""Diagnostic de la ventilation et des auxiliaires."""
def diagnose_ventilation(data: dict, rules: dict) -> dict:
    if not data.get("has_ventilation", False):
        return {"alerts": ["Absence de ventilation mécanique déclarée : vérifier les exigences sanitaires."],
                "actions": ["Vérifier les dispositifs de renouvellement d'air et les conditions réglementaires."],
                "status": "à vérifier"}
    alerts, actions = [], [
        "Mesurer les débits d'air aux terminaux et les comparer aux besoins d'occupation.",
        "Contrôler filtres, courroies, moteurs, variateurs et pertes de charge.",
        "Vérifier l'équilibrage des réseaux et la récupération de chaleur."
    ]
    schedule = data.get("ventilation_schedule_hours_day")
    if schedule is not None and float(schedule) > 18:
        alerts.append("Ventilation déclarée en fonctionnement plus de 18 h/j : confronter aux horaires d'occupation.")
    return {"alerts": alerts, "actions": actions, "status": "à investiguer"}

"""Diagnostic du poste chauffage : règles de screening, non réglementaires."""
def diagnose_heating(data: dict, rules: dict) -> dict:
    alerts, actions = [], []
    gas = float(data.get("gas_kwh", 0) or 0)
    district = float(data.get("district_kwh", 0) or 0)
    kind = (data.get("heating_type") or "unknown").lower()
    if gas > 0 and kind in ("unknown", "gaz", "chaudiere gaz", "chaudière gaz"):
        alerts.append("La part de gaz peut inclure chauffage et ECS : vérifier la séparation des usages.")
        actions.append("Relever la chaudière, le rendement, les températures départ/retour et la régulation.")
    if kind == "electric":
        actions.append("Contrôler les émetteurs, la programmation, les consignes et les auxiliaires.")
    if kind == "heat_pump":
        actions.append("Contrôler le COP saisonnier, les températures d'eau et les cycles courts.")
    if district > 0:
        actions.append("Vérifier la sous-station, l'échangeur, l'équilibrage et les températures du réseau.")
    if data.get("heating_setpoint_c") is not None and float(data["heating_setpoint_c"]) > 20:
        alerts.append("Consigne de chauffage supérieure à 20 °C : vérifier le confort et les dérives.")
        actions.append("Tester une baisse progressive de consigne compatible avec l'usage.")
    return {"alerts": alerts, "actions": actions, "status": "à investiguer" if alerts or actions else "non caractérisé"}

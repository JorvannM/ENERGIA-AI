"""Moteur de priorisation des recommandations energetiques."""

def prioritize_recommendations(recommendations):
    """Enrichit les recommandations sans modifier les calculs existants."""
    enriched = []

    for recommendation in recommendations:
        item = recommendation.copy()
        evidence = item.get("evidence") or []
        checks = item.get("checks") or []
        simulation = item.get("simulation") or {}

        if evidence:
            priority = "Verification prioritaire"
            action_type = "verification"
        elif simulation.get("available") and simulation.get("savings_kwh_year", 0) > 0:
            priority = "Amelioration a etudier"
            action_type = "optimization"
        else:
            priority = "A qualifier"
            action_type = "investigation"

        item["priority"] = priority
        item["action_type"] = action_type
        item["confidence"] = "indicative"
        item["verification_required"] = bool(checks)

        enriched.append(item)

    return enriched

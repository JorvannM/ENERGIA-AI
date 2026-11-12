"""Préremplissage contrôlé et traçable depuis un DPE choisi explicitement."""
from services.building_matcher import first

FIELDS = {
    "construction_year": ("Année_construction", "annee_construction"),
    "heating_energy": ("Type_énergie_n°1", "Type_énergie_principale_chauffage", "type_energie_principale_chauffage", "Type_energie_principale_chauffage"),
    "heating_system": ("Type_installation_chauffage", "Type_générateur_chauffage_principal", "Type_generateur_chauffage_principal", "Type_émetteur_chauffage", "Type_emetteur_chauffage"),
    "ventilation_type": ("Type_ventilation", "type_ventilation", "Type_ventilation_(général)", "Type_ventilation_(general)"),
    "dhw_type": ("Type_générateur_ECS", "Type_generateur_ECS", "Type_énergie_ECS", "Type_energie_ECS", "Type_énergie_n°1_ECS"),
    "cooling_type": ("Type_générateur_froid", "Type_generateur_froid", "Type_installation_refroidissement"),
    "wall_insulation": ("Isolation_mur", "Isolation_murs", "Type_isolation_mur"),
    "roof_insulation": ("Isolation_toiture", "Type_isolation_plancher_haut"),
    "glazing": ("Type_vitrage", "Type_vitrage_principal"),
    "building_use": ("Type_bâtiment", "Type_batiment", "Type_usage", "Type_bâtiment_(DPE)"),
    "energy_class": ("Etiquette_DPE", "etiquette_dpe"),
    "ghg_class": ("Etiquette_GES", "etiquette_ges"),
}

def approved_prefill(candidate):
    raw = candidate.get("raw") or {}
    source = candidate.get("source", "DPE")
    result = {"source": source, "dpe_id": candidate.get("id"), "field_sources": {}, "missing": []}
    for key in ("surface_m2", "construction_year", "heating_type", "energy_class", "ghg_class"):
        value = candidate.get(key)
        if value not in (None, ""):
            result[key] = value
            result["field_sources"][key] = source
    for key, aliases in FIELDS.items():
        value = first(raw, *aliases)
        if value not in (None, ""):
            result[key] = str(value)
            result["field_sources"][key] = source
        elif key not in result:
            result["missing"].append(key)
    result["surface_type"] = candidate.get("surface_type")
    result["scope_warning"] = candidate.get("warning", "Vérifier le périmètre du DPE.")
    return result

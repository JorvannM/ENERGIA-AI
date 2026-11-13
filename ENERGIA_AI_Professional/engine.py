"""Orchestrateur HVAC Building et API de compatibilité avec l'ancienne interface."""
from __future__ import annotations
import json, os
from pathlib import Path
from data_model import BuildingData, normalize_building
from validation import validate_building
from heating import diagnose_heating
from cooling import diagnose_cooling
from ventilation import diagnose_ventilation
from lighting import diagnose_lighting
from hot_water import diagnose_hot_water
from exploitation import diagnose_operation
from economics import estimate_economics as estimate_economics_module
from carbon import estimate_carbon as carbon_module_estimate
from recommendations import build_recommendations as recommendations_module
from diagnostic_expert import generate_detailed_diagnostics
from assistant_local import generate_local_answer
ROOT = Path(__file__).parent

def load_rules(path=None):
    with (Path(path) if path else ROOT/"data"/"diagnostics_rules.json").open(encoding="utf-8") as f:
        return json.load(f)

def analyse_building(surface, electricity, gas, district, annual_cost, **kwargs):
    raw = {
        "surface_m2": surface, "electricity_kwh": electricity, "gas_kwh": gas,
        "district_kwh": district, "annual_energy_cost_eur": annual_cost,
        **kwargs
    }
    data = normalize_building(raw)
    validation = validate_building(data)
    if not validation["valid"]:
        raise ValueError(" ".join(validation["errors"]))
    total = sum(float(data[k] or 0) for k in ("electricity_kwh","gas_kwh","district_kwh","other_kwh"))
    surface = float(data["surface_m2"])
    period_months = float(data["data_period_months"])
    annualization_factor = 12.0 / period_months
    data["annualized_total_kwh"] = total * annualization_factor
    data["annualized_intensity_kwh_m2_year"] = (
        total * annualization_factor / surface
    )
    data["annualization_method"] = (
        "measured_12_months" if period_months == 12
        else "linear_extrapolation"
    )
    data["annualization_warning"] = (
        "" if period_months == 12
        else "Estimation indicative sans correction de saisonnalite."
    )
    data.update({
        "surface": surface, "electricity": float(data["electricity_kwh"]),
        "gas": float(data["gas_kwh"]), "district": float(data["district_kwh"]),
        "total_kwh": total, "intensity": total/surface,
        "annual_cost": float(data["annual_energy_cost_eur"]),
        "price_per_kwh": float(data["annual_energy_cost_eur"])/total if total else 0.0,
        "electricity_share": float(data["electricity_kwh"])/total if total else 0.0,
        "gas_share": float(data["gas_kwh"])/total if total else 0.0,
        "district_share": float(data["district_kwh"])/total if total else 0.0,
        "data_status": "Données déclarées par l'utilisateur",
        "data_period": f"{data['data_period_months']} mois",
        "validation": validation
    })
    return data

def diagnose_building(data):
    rules = load_rules()
    modules = {
        "heating": diagnose_heating(data, rules),
        "cooling": diagnose_cooling(data, rules),
        "ventilation": diagnose_ventilation(data, rules),
        "lighting": diagnose_lighting(data, rules),
        "hot_water": diagnose_hot_water(data, rules),
        "operation": diagnose_operation(data, rules)
    }
    alerts = []
    for key, result in modules.items():
        for alert in result.get("alerts", []):
            alerts.append({"level":"À investiguer","title":key.replace("_"," ").title(),"detail":alert})
    intensity = float(
        data.get(
            "annualized_intensity_kwh_m2_year",
            data.get("intensity", 0)
        ) or 0
    )
    if data.get("annualization_method") == "linear_extrapolation":
        alerts.append({
            "level": "Vigilance",
            "title": "Consommation annualisee indicative",
            "detail": (
                "Consommation extrapolee a 12 mois sans correction "
                "de saisonnalite. Confirmer avec des donnees annuelles."
            )
        })
    threshold = rules["screening_thresholds"]
    if data.get("total_kwh",0) == 0:
        alerts.insert(0, {"level":"Donnée manquante","title":"Aucune consommation renseignée",
                          "detail":"Le diagnostic énergétique ne peut pas être interprété sans consommation annuelle."})
    elif intensity >= threshold["high_kwh_m2_year"]:
        alerts.append({"level":"À investiguer","title":"Intensité énergétique très élevée",
                       "detail":f"{intensity:.1f} kWh/m²/an : vérifier périmètre, usage et période."})
    elif intensity >= threshold["elevated_kwh_m2_year"]:
        alerts.append({"level":"Vigilance","title":"Intensité énergétique élevée",
                       "detail":f"{intensity:.1f} kWh/m²/an : comparer à des bâtiments de même usage."})
    return {
    "modules": modules,
    **modules,
    "alerts": alerts,
    "detailed_diagnostics": generate_detailed_diagnostics(data),
    "observations": [
        "Pré-diagnostic indicatif : confirmer les constats par visite et mesures."
    ],
    "confidence": (
        "Confiance dépendante de la qualité et "
        "de la granularité des données."
    )
}

def build_recommendations(data):
    diagnosis = diagnose_building(data)
    recommendations = recommendations_module(diagnosis, data)

    from lighting_savings import simulate_led_savings

    if data.get("has_lighting", True):
        led = simulate_led_savings(data)

        if led["available"] and led["savings_kwh_year"] > 0:
            from lighting_economics import simulate_led_economics
            led_economics = simulate_led_economics(data)
            recommendations.append({
                "title": "Remplacement des luminaires par des LED",
                "detail": (
                    f"Economie theorique : {led['savings_kwh_year']} kWh/an "
                    f"({led['savings_pct']} % du poste eclairage)."
                ),
                "category": "Eclairage",
                "priority": "A qualifier",
                "basis": led["assumption"],
                "savings_low_pct": 0,
                "savings_high_pct": led["savings_pct"],
                "checks": [
                    "Verifier les puissances reelles",
                    "Confirmer les horaires de fonctionnement"
                ],
                "evidence": [],
                "savings_note": (
                    "Simulation technique indicative, "
                    "sans garantie de gains reels."
                ),
                "simulation": led,
                "economics": led_economics
            })

    return recommendations

def estimate_savings(data, recommendations):
    # Ne pas additionner des gains par poste sans sous-comptage : enveloppe conservatrice globale.
    if not data.get("total_kwh") or not recommendations:
        return {"low_kwh":0.0,"high_kwh":0.0,"low_eur":0.0,"high_eur":0.0,"low_pct":0.0,"high_pct":0.0}
    low, high = (3.0, 10.0) if data.get("meter_separation") else (2.0, 7.0)
    return {"low_kwh":data["total_kwh"]*low/100, "high_kwh":data["total_kwh"]*high/100,
            "low_eur":data["annual_cost"]*low/100, "high_eur":data["annual_cost"]*high/100,
            "low_pct":low,"high_pct":high,
            "warning":"Fourchette indicative globale, non additive et à confirmer par étude."}

def estimate_carbon(data, factors=None):
    normalized = dict(data)
    for old,new in (("electricity","electricity_kwh"),("gas","gas_kwh"),("district","district_kwh")):
        if new not in normalized: normalized[new] = normalized.get(old,0)
    result = carbon_module_estimate(normalized, factors)
    # Compatibilité avec l'ancienne interface
    result["total_kg"] = result["total_kgco2e"]
    result["total_tonnes"] = result["total_tco2e"]
    result["by_energy_kg"] = result["by_energy_kgco2e"]
    return result


def ask_ai(question, data, recommendations):
    """
    Conseiller énergétique automatique local.
    Fonctionne sans clé API et sans connexion OpenAI.
    """
    try:
        diagnosis = diagnose_building(data)

        answer = generate_local_answer(
            question=question,
            data=data,
            recommendations=recommendations,
            diagnosis=diagnosis
        )

        return answer, "Assistant expert local"

    except Exception as exc:
        return (
            f"Impossible de générer la réponse locale : "
            f"{type(exc).__name__} — {exc}",
            "Erreur locale"
        )

    try:
        from openai import OpenAI
        response = OpenAI().responses.create(
            model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
            instructions=("Tu es un ingénieur conseil en efficacité énergétique des bâtiments. "
                          "Réponds en français, distingue mesures, déclarations et hypothèses. "
                          "Ne présente jamais ce pré-diagnostic comme un audit réglementaire."),
            input=f"Question : {question}\nDonnées : {data}\nRecommandations : {recommendations}"
        )
        return response.output_text, "OpenAI API"
    except Exception as exc:
        return f"IA distante indisponible ({exc}). Le diagnostic local reste accessible.", "Mode local"

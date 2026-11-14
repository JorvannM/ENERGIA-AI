
"""Assistant technique local HVAC Building — sans API externe."""

import unicodedata


def normalize_text(text):
    text = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def generate_local_answer(question, data, recommendations, diagnosis, analysis_context=None):
    q = normalize_text(question)

    # Analyse contextuelle des questions sur l'electricite.
    if analysis_context and any(
        word in q for word in (
            "electricite",
            "electrique",
            "kwh electrique",
            "consommation elec"
        )
    ):
        from advisor_intelligence import answer_electricity
        return answer_electricity(analysis_context)

    # Analyse economique prioritaire lorsque la question
    # porte sur les gains, les couts ou les investissements.
    if analysis_context:
        from advisor_intelligence import answer_economics

        economic_answer = answer_economics(
            question,
            analysis_context
        )

        if economic_answer is not None:
            return economic_answer

    # Analyse contextuelle des postes energetiques.
    if analysis_context:
        from advisor_intelligence import answer_energy_topic

        technical_answer = answer_energy_topic(
            question,
            analysis_context
        )

        if technical_answer is not None:
            return technical_answer

    total = float(data.get("total_kwh", 0) or 0)
    intensity = float(data.get("intensity", 0) or 0)
    surface = float(data.get("surface_m2", 0) or 0)
    cost = float(data.get("annual_cost", 0) or 0)

    lines = [
        "### Analyse énergétique du bâtiment",
        f"- Surface : {surface:,.0f} m²",
        f"- Consommation totale : {total:,.0f} kWh/an",
        f"- Intensité énergétique : {intensity:,.1f} kWh/m²/an",
        f"- Dépenses annuelles : {cost:,.0f} €",
        ""
    ]

    alerts = diagnosis.get("alerts", [])
    detailed = diagnosis.get("detailed_diagnostics", [])

    def add_diagnostics():
        lines.append("### Anomalies et points de vigilance")

        if not alerts and not detailed:
            lines.append(
                "Aucune anomalie détectée avec les données disponibles. "
                "Cela ne garantit pas l'absence de défaut."
            )

        for item in alerts[:5]:
            lines.append(
                f"- **{item.get('title', 'Alerte')}** : "
                f"{item.get('detail', '')}"
            )

        for item in detailed[:5]:
            lines.append(
                f"- **{item.get('title', 'Diagnostic')}** : "
                f"{item.get('cause', '')}"
            )
            for check in item.get("checks", [])[:2]:
                lines.append(f"  - Contrôle : {check}")

    def add_recommendations():
        lines.append("")
        lines.append("### Actions recommandées")

        if not recommendations:
            lines.append(
                "Les données disponibles ne permettent pas encore "
                "de proposer un plan d'action précis."
            )

        for index, item in enumerate(recommendations[:5], 1):
            lines.append(
                f"{index}. **{item.get('title', 'Action')}** — "
                f"{item.get('detail', '')}"
            )
            checks = item.get("checks", [])
            if checks:
                lines.append(f"   - À vérifier : {checks[0]}")

    if any(word in q for word in [
        "anomalie", "probleme", "defaut", "diagnostic",
        "surconsommation", "pourquoi"
    ]):
        add_diagnostics()
        add_recommendations()

    elif any(word in q for word in [
        "econom", "optimis", "amelior", "recommand",
        "priorit", "solution", "action"
    ]):
        add_recommendations()

    elif any(word in q for word in [
        "consommation", "energie", "performance", "bilan"
    ]):
        lines.append("### Interprétation")
        lines.append(
            "L'intensité énergétique est un indicateur global. "
            "Elle doit être interprétée selon l'usage, "
            "l'occupation et les caractéristiques du bâtiment."
        )
        add_diagnostics()

    else:
        lines.append("### Synthèse technique")
        lines.append(
            "Voici les principaux constats issus du "
            "pré-diagnostic énergétique disponible."
        )
        add_diagnostics()
        add_recommendations()

    lines.extend([
        "",
        "---",
        "*Réponse automatique locale fondée sur les données "
        "renseignées et les règles métier. "
        "Elle ne constitue pas un audit réglementaire.*"
    ])

    return "\n".join(lines)

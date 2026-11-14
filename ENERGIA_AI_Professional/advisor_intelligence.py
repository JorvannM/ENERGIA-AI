"""Analyse technique contextualisee pour IA Advisor."""

from __future__ import annotations


def answer_electricity(context: dict) -> str:
    breakdown = context.get("energy_breakdown") or {}
    intelligence = context.get("energy_intelligence") or {}

    energies = breakdown.get("by_energy") or {}
    electricity = energies.get("electricity") or {}

    total = float(breakdown.get("total_kwh_year") or 0)
    electric_kwh = float(electricity.get("kwh_year") or 0)

    share = 100 * electric_kwh / total if total > 0 else None

    lines = [
        "### Analyse de la consommation electrique",
        "",
        f"Consommation electrique declaree : {electric_kwh:,.0f} kWh/an.",
    ]

    if share is not None:
        lines.append(
            f"Part de l'electricite dans le bilan : {share:.1f} %."
        )

    lines.extend([
        "",
        "### Interpretation",
        (
            "Cette proportion ne suffit pas a demontrer une "
            "surconsommation. Il faut examiner les usages, "
            "les horaires et les equipements."
        ),
    ])

    uses = breakdown.get("by_use") or {}
    quantified = [
        (item.get("label", key), item.get("kwh_year"))
        for key, item in uses.items()
        if isinstance(item, dict) and item.get("kwh_year") is not None
    ]

    if quantified:
        lines.extend(["", "### Postes quantifies"])
        for label, value in quantified:
            lines.append(f"- {label} : {float(value):,.0f} kWh/an")
        lines.append(
            "Ces estimations ne constituent pas necessairement "
            "des consommations electriques mesurees."
        )
    else:
        lines.extend([
            "",
            "### Limites des donnees",
            (
                "Aucun poste energetique n'est quantifie "
                "individuellement. Il est impossible d'attribuer "
                "la consommation electrique a un equipement precis."
            ),
        ])

    observations = intelligence.get("observations") or []
    warnings = [
        item for item in observations
        if isinstance(item, dict)
        and item.get("severity") in ("warning", "critical")
    ]

    if warnings:
        lines.extend(["", "### Points de vigilance"])
        for item in warnings[:3]:
            lines.append(
                f"- {item.get('title', 'Observation')} : "
                f"{item.get('detail', '')}"
            )

    lines.extend([
        "",
        "### Prochaines verifications",
        "- Identifier les usages alimentes en electricite.",
        "- Relever les horaires reels de fonctionnement.",
        "- Comparer les consommations avec les puissances installees.",
        "- Mettre en place un sous-comptage si necessaire.",
        "",
        (
            "*Analyse indicative fondee sur les donnees disponibles. "
            "Aucune economie n'est garantie.*"
        ),
    ])

    return "\n".join(lines)


ENERGY_TOPICS = {
    "heating": {
        "label": "chauffage",
        "keywords": ("chauffage", "chauffer", "chaudiere", "radiateur"),
        "categories": ("chauffage",),
    },
    "cooling": {
        "label": "climatisation",
        "keywords": ("climatisation", "climatiseur", "refroidissement", "froid"),
        "categories": ("climatisation", "refroidissement"),
    },
    "ventilation": {
        "label": "ventilation",
        "keywords": ("ventilation", "vmc", "debit d'air"),
        "categories": ("ventilation",),
    },
    "lighting": {
        "label": "eclairage",
        "keywords": ("eclairage", "luminaire", "led", "lampe"),
        "categories": ("eclairage",),
    },
}


def _normalize(text):
    import unicodedata
    value = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in value if not unicodedata.combining(c))


def answer_energy_topic(question: str, context: dict) -> str | None:
    """Repond aux questions sur un poste a partir des resultats existants."""
    q = _normalize(question)

    selected = None
    for key, config in ENERGY_TOPICS.items():
        if any(word in q for word in config["keywords"]):
            selected = key
            break

    if selected is None:
        return None

    config = ENERGY_TOPICS[selected]
    breakdown = context.get("energy_breakdown") or {}
    uses = breakdown.get("by_use") or {}
    use = uses.get(selected) or {}

    lines = [
        "### Analyse du poste : " + config["label"],
        "",
    ]

    consumption = use.get("kwh_year")
    source = use.get("source", "not_quantified")

    if consumption is None:
        lines.append(
            "La consommation propre a ce poste n'est pas quantifiee "
            "avec les donnees actuellement disponibles."
        )
    else:
        lines.append(
            f"Consommation indicative du poste : "
            f"{float(consumption):,.0f} kWh/an."
        )
        lines.append("Origine de la valeur : " + str(source) + ".")

    recommendations = context.get("recommendations") or []
    matches = [
        item for item in recommendations
        if isinstance(item, dict)
        and _normalize(item.get("category", "")) in config["categories"]
    ]

    # Examiner directement le simulateur correspondant.
    from simulation_intelligence import inspect_simulations

    data = context.get("data") or {}
    simulation_info = inspect_simulations(data).get(selected, {})

    lines.extend(["", "### Etat de la simulation"])

    if simulation_info.get("available"):
        result = simulation_info.get("result") or {}

        lines.append("Simulation technique disponible.")

        gain = result.get("savings_kwh_year")
        if gain is not None:
            lines.append(
                f"Economie theorique : {float(gain):,.0f} kWh/an."
            )

        assumption = result.get("assumption")
        if assumption:
            lines.append("Hypotheses : " + str(assumption))

    else:
        missing = simulation_info.get("missing_fields") or []

        if missing:
            lines.append(
                "Donnees necessaires pour activer la simulation :"
            )

            for field in missing:
                lines.append("- " + field["label"])
        else:
            lines.append(
                "Simulation indisponible : "
                + str(simulation_info.get("reason") or
                      "parametres a verifier")
            )

    lines.extend(["", "### Actions et simulations disponibles"])

    if not matches:
        lines.append(
            "Aucune action specifique n'est actuellement documentee "
            "pour ce poste."
        )

    for item in matches[:5]:
        lines.append(
            "- " + str(item.get("title", "Action a etudier"))
        )

        simulation = item.get("simulation") or {}

        if simulation.get("available"):
            gain = simulation.get("savings_kwh_year")
            if gain is not None:
                lines.append(
                    f"  - Economie theorique : "
                    f"{float(gain):,.0f} kWh/an."
                )

            percentage = simulation.get("savings_pct")
            if percentage is not None:
                lines.append(
                    f"  - Reduction theorique : "
                    f"{float(percentage):.1f} %."
                )

        economics = item.get("economics") or {}

        if economics.get("available"):
            annual = economics.get("annual_savings_eur")
            if annual is not None:
                lines.append(
                    f"  - Gain financier estime : "
                    f"{float(annual):,.2f} EUR/an."
                )

            payback = economics.get("payback_years")
            if payback is not None:
                lines.append(
                    f"  - Retour simple estime : "
                    f"{float(payback):.1f} ans."
                )

        checks = item.get("checks") or []
        if checks:
            lines.append(
                "  - Verification necessaire : " + str(checks[0])
            )

    lines.extend([
        "",
        "### Interpretation technique",
        (
            "Les resultats presentes dependent des hypotheses "
            "et des parametres renseignes. Les gains de plusieurs "
            "simulations ne doivent pas etre additionnes sans "
            "verification des interactions."
        ),
        "",
        (
            "*Analyse indicative. Une verification technique "
            "est necessaire avant toute decision d'investissement.*"
        ),
    ])

    return "\n".join(lines)


def answer_economics(question: str, context: dict) -> str | None:
    """Compare les simulations disponibles sans additionner les gains."""
    q = _normalize(question)

    keywords = (
        "rentab", "investissement", "retour sur",
        "amortissement", "cout", "financier",
        "euro", "budget", "econom", "gain",
        "quelle solution", "quelle action",
        "plus interessant", "priorit"
    )

    if not any(word in q for word in keywords):
        return None

    recommendations = context.get("recommendations") or []
    options = []

    # Identifier un equipement mentionne dans la question.
    selected_topic = None
    for key, config in ENERGY_TOPICS.items():
        if any(word in q for word in config["keywords"]):
            selected_topic = key
            break

    # Filtrer les actions pour les questions economiques ciblees.
    if selected_topic:
        allowed_categories = ENERGY_TOPICS[selected_topic]["categories"]
        recommendations = [
            item for item in recommendations
            if isinstance(item, dict)
            and _normalize(item.get("category", "")) in allowed_categories
        ]

    for item in recommendations:
        if not isinstance(item, dict):
            continue

        simulation = item.get("simulation") or {}
        economics = item.get("economics") or {}

        if not simulation.get("available"):
            continue

        gain = simulation.get("savings_kwh_year")

        if not isinstance(gain, (int, float)) or gain <= 0:
            continue

        options.append({
            "title": item.get("title", "Action"),
            "gain": gain,
            "economics": economics,
            "checks": item.get("checks") or [],
        })

    asks_profitability = any(
        word in q for word in (
            "rentab", "retour sur", "amortissement",
            "investissement", "payback"
        )
    )

    if asks_profitability:
        options.sort(
            key=lambda item: (
                not isinstance(
                    item["economics"].get("payback_years"),
                    (int, float)
                ),
                (
                    item["economics"]["payback_years"]
                    if isinstance(
                        item["economics"].get("payback_years"),
                        (int, float)
                    )
                    else float("inf")
                ),
                -item["gain"]
            )
        )
    else:
        options.sort(
            key=lambda item: item["gain"],
            reverse=True
        )

    lines = [
        (
            "### Analyse de rentabilite"
            if asks_profitability
            else "### Comparaison des solutions energetiques"
        ),
        ""
    ]

    if asks_profitability:
        lines.extend([
            "La rentabilite depend des couts d'investissement, "
            "des economies financieres annuelles et des "
            "hypotheses d'exploitation.",
            "",
            "Les economies en kWh ne suffisent pas "
            "pour identifier l'investissement le plus rentable.",
            ""
        ])

    if not options:
        lines.append(
            "Aucune simulation d'economies exploitable "
            "n'est disponible pour ce batiment."
        )

        from simulation_intelligence import inspect_simulations

        data = context.get("data") or {}
        simulations = inspect_simulations(data)

        if selected_topic:
            simulations = {
                selected_topic: simulations[selected_topic]
            }

        lines.extend([
            "",
            "### Donnees necessaires pour calculer les economies"
        ])

        for simulation in simulations.values():
            lines.append("")
            lines.append("**" + simulation["label"] + "**")

            missing = simulation.get("missing_fields") or []

            if missing:
                for field in missing:
                    lines.append("- " + field["label"])
            elif not simulation.get("available"):
                lines.append(
                    "- " + str(
                        simulation.get("reason")
                        or "Parametres a verifier."
                    )
                )
            else:
                lines.append(
                    "- Simulation disponible, mais aucune "
                    "economie positive exploitable."
                )
    else:
        for index, option in enumerate(options, 1):
            lines.append(
                f"{index}. {option['title']}"
            )
            lines.append(
                f"   - Economie theorique : "
                f"{option['gain']:,.0f} kWh/an."
            )

            eco = option["economics"]

            if eco.get("available"):
                annual = eco.get("annual_savings_eur")
                payback = eco.get("payback_years")

                if isinstance(annual, (int, float)):
                    lines.append(
                        f"   - Gain financier estime : "
                        f"{annual:,.2f} EUR/an."
                    )

                if isinstance(payback, (int, float)):
                    lines.append(
                        f"   - Retour simple estime : "
                        f"{payback:.1f} ans."
                    )
            else:
                lines.append(
                    "   - Gain financier non calcule : "
                    "donnees economiques insuffisantes."
                )

            if not isinstance(
                eco.get("payback_years"), (int, float)
            ):
                lines.append(
                    "   - Temps de retour non determine : "
                    "cout d'investissement ou gain financier manquant."
                )

            if option["checks"]:
                lines.append(
                    "   - A verifier : " + str(option["checks"][0])
                )

    lines.extend([
        "",
        "### Interpretation",
        (
            (
                "Les solutions avec un temps de retour calcule "
                "sont classees du plus court au plus long. "
                "Les autres ne peuvent pas etre comparees "
                "financierement avec les donnees disponibles."
            )
            if asks_profitability
            else (
                "Les solutions sont classees par economie energetique "
                "theorique decroissante, et non par rentabilite. "
                "Une economie plus importante ne signifie pas "
                "necessairement un meilleur investissement."
            )
        ),
        "",
        (
            "Les gains peuvent se recouper : ils ne doivent pas "
            "etre additionnes sans analyse des interactions."
        ),
        "",
        (
            "*Estimations indicatives, a confirmer par "
            "une etude technique et economique.*"
        )
    ])

    return "\n".join(lines)

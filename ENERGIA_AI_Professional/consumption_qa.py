"""Questions-reponses fondees sur les consommations importees."""

import unicodedata


def _normalize(value):
    value = unicodedata.normalize("NFKD", str(value).lower())
    return "".join(
        char for char in value
        if not unicodedata.combining(char)
    )


def _number(value):
    return f"{float(value):,.0f}".replace(",", " ")


def answer_consumption_question(question, report):
    """Repondre uniquement avec les indicateurs disponibles."""

    if not isinstance(report, dict) or not report:
        return {
            "answered": False,
            "answer": "Importez d'abord un fichier de consommations.",
            "source": "consumption_session",
        }

    q = _normalize(question)

    analysis = report.get("analysis") or {}
    anomalies = report.get("anomalies") or {}
    comparison = report.get("comparison") or {}

    if any(word in q for word in (
        "anomalie", "anormal", "suspect", "alerte"
    )):
        count = anomalies.get("anomaly_count", 0)

        return {
            "answered": True,
            "answer": (
                f"{count} signalement(s) statistique(s) "
                "ont ete identifies. Ces alertes ne prouvent "
                "pas un dysfonctionnement. Verifiez les releves, "
                "les conditions climatiques et l'occupation."
            ),
            "source": "consumption_anomalies",
        }

    if any(word in q for word in (
        "augmentation", "augmente", "baisse",
        "evolution", "variation", "compare",
        "comparaison"
    )):
        items = comparison.get("comparisons") or []
        valid = [
            item for item in items
            if item.get("comparable")
            and item.get("variation_pct") is not None
        ]

        if not valid:
            answer = (
                "Les donnees ne permettent pas une comparaison "
                "annuelle fiable. Deux annees completes sont "
                "necessaires pour chaque energie."
            )
        else:
            parts = []

            for item in valid:
                parts.append(
                    f"{item['energy']} : "
                    f"{item['previous_year']} vers "
                    f"{item['current_year']} : "
                    f"{item['variation_pct']:+.1f} %."
                )

            answer = " ".join(parts)
            answer += (
                " Ces variations ne sont pas corrigees "
                "de la meteo ni de l'occupation."
            )

        return {
            "answered": True,
            "answer": answer,
            "source": "consumption_comparison",
        }

    if any(word in q for word in (
        "pic", "maximum", "plus eleve", "plus forte",
        "mois le plus", "mois maximum"
    )):
        peak = analysis.get("peak_month")

        if peak:
            answer = (
                f"Le maximum observe est en "
                f"{peak['month']:02d}/{peak['year']} : "
                f"{_number(peak['kwh'])} kWh. "
                "La cause ne peut pas etre determinee "
                "avec cette seule information."
            )
        else:
            answer = "Aucun mois maximum n'est disponible."

        return {
            "answered": True,
            "answer": answer,
            "source": "consumption_analysis",
        }

    if any(word in q for word in (
        "total", "bilan", "combien", "consommation"
    )):
        total = analysis.get("total_kwh")

        if total is None:
            answer = "Le total des consommations est indisponible."
        else:
            answer = (
                f"Le total des consommations importees est "
                f"de {_number(total)} kWh, sur les periodes "
                "renseignees dans le fichier."
            )

        return {
            "answered": True,
            "answer": answer,
            "source": "consumption_analysis",
        }

    return {
        "answered": False,
        "answer": (
            "Je peux analyser le bilan, les pics, "
            "les anomalies et les evolutions annuelles "
            "des consommations importees."
        ),
        "source": "consumption_qa",
    }

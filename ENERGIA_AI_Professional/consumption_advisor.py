"""Conseiller energetique fonde sur les donnees importees."""


def generate_consumption_insights(
    analysis,
    anomalies=None,
    comparison=None
):
    """Produire des observations explicables et factuelles."""

    insights = []

    if not analysis or not analysis.get("available"):
        return {
            "available": False,
            "insights": [],
            "message": "Aucune consommation exploitable."
        }

    total = analysis.get("total_kwh", 0)
    average = analysis.get("average_monthly_kwh", 0)
    peak = analysis.get("peak_month")

    insights.append({
        "category": "consumption",
        "priority": "info",
        "title": "Bilan des consommations",
        "message": (
            f"Consommation totale : {total:,.0f} kWh. "
            f"Moyenne par mois renseigne : {average:,.0f} kWh."
        )
    })

    if peak:
        insights.append({
            "category": "peak",
            "priority": "info",
            "title": "Periode de consommation maximale",
            "message": (
                f"Le maximum observe concerne "
                f"{peak['month']:02d}/{peak['year']} "
                f"avec {peak['kwh']:,.0f} kWh. "
                "Ce constat ne suffit pas a identifier la cause."
            )
        })

    if anomalies:
        count = anomalies.get("anomaly_count", 0)

        if count:
            insights.append({
                "category": "anomalies",
                "priority": "warning",
                "title": "Anomalies a examiner",
                "message": (
                    f"{count} signalement(s) statistique(s) "
                    "ont ete identifies. Verifier les releves, "
                    "la meteo et les horaires d'occupation."
                )
            })

    if comparison:
        for item in comparison.get("comparisons", []):
            if not item.get("comparable"):
                continue

            variation = item.get("variation_pct")

            if variation is None:
                continue

            insights.append({
                "category": "annual_comparison",
                "priority": (
                    "warning" if variation > 10 else "info"
                ),
                "title": (
                    "Evolution annuelle : " +
                    item["energy"]
                ),
                "message": (
                    f"Entre {item['previous_year']} et "
                    f"{item['current_year']}, la consommation "
                    f"a varie de {variation:+.1f} %. "
                    "Cette variation n'est pas corrigee "
                    "des conditions climatiques ou d'occupation."
                )
            })

    return {
        "available": True,
        "insights": insights,
        "method": "Analyse hybride fondee sur des indicateurs calcules",
        "limitations": (
            "Les observations ne constituent pas un "
            "diagnostic causal. Une verification technique "
            "reste necessaire."
        )
    }

"""Questions-reponses pour l'analyse energetique combinee."""

import unicodedata


def normalize(text):
    value = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(
        c for c in value
        if not unicodedata.combining(c)
    )


def answer_combined_question(question, combined):
    """Generer une reponse factuelle depuis l'analyse croisee."""

    if not isinstance(combined, dict):
        return {
            "answered": False,
            "answer": "Analyse combinee indisponible."
        }

    q = normalize(question)
    observations = combined.get("observations") or []
    limitations = combined.get("limitations") or []

    if any(word in q for word in (
        "ecart", "difference", "estime", "reel", "mesure"
    )):
        estimated = combined.get("estimated_annual_kwh")
        measured = combined.get("measured_annual_kwh")
        gap = combined.get("gap_pct")

        if gap is None:
            answer = (
                "Une comparaison annuelle fiable n'est pas "
                "disponible. Il faut verifier les periodes "
                "et les usages energetiques couverts."
            )
        else:
            answer = (
                f"Estimation : {estimated:,.0f} kWh/an. "
                f"Mesure : {measured:,.0f} kWh/an. "
                f"Ecart indicatif : {gap:+.1f} %. "
                "Cet ecart ne prouve pas un dysfonctionnement."
            )

    elif any(word in q for word in (
        "anomalie", "alerte", "suspect", "inhabituel"
    )):
        selected = [
            item.get("message", "")
            for item in observations
            if item.get("category") == "anomalies"
        ]

        answer = (
            " ".join(selected)
            if selected
            else "Aucune anomalie n'est signalee dans la synthese."
        )

    elif any(word in q for word in (
        "augmentation", "augmente", "baisse",
        "evolution", "variation"
    )):
        selected = [
            item.get("message", "")
            for item in observations
            if item.get("category") == "annual_change"
        ]

        answer = (
            " ".join(selected)
            if selected
            else "Aucune evolution annuelle comparable n'est disponible."
        )

    elif any(word in q for word in (
        "pourquoi", "cause", "origine", "raison"
    )):
        answer = (
            "Les donnees disponibles ne permettent pas "
            "d'attribuer une cause certaine aux variations. "
            "Il convient de verifier les conditions meteo, "
            "les horaires d'occupation, les reglages CVC, "
            "les equipements et les releves des compteurs."
        )

    elif any(word in q for word in (
        "limite", "fiabilite", "precision", "methode"
    )):
        answer = (
            " ".join(limitations)
            if limitations
            else "Les limites de l'analyse ne sont pas renseignees."
        )

    else:
        messages = [
            item.get("message", "")
            for item in observations
            if item.get("message")
        ]

        answer = (
            " ".join(messages)
            if messages
            else "Aucune observation croisee exploitable."
        )

    return {
        "answered": True,
        "answer": answer,
        "source": "combined_energy_analysis",
        "limitations": limitations
    }

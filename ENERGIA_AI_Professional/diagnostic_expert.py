
"""Moteur de diagnostic expert HVAC Building."""

def generate_detailed_diagnostics(data):
    diagnostics = []

    def add(category, title, severity, cause, evidence, checks, actions, confidence):
        diagnostics.append({
            "category": category,
            "title": title,
            "severity": severity,
            "cause": cause,
            "evidence": evidence,
            "checks": checks,
            "actions": actions,
            "confidence": confidence
        })

    def number(key, default=None):
        try:
            value = data.get(key)
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    # 1. Consommation énergétique
    intensity = number("intensity")
    period = number("data_period_months", 12)

    if intensity is not None and period == 12:
        if intensity >= 400:
            add(
                "Énergie",
                "Intensité énergétique très élevée",
                "Élevée",
                "Périmètre de consommation, surface ou usages à vérifier.",
                f"Intensité déclarée : {intensity:.1f} kWh/m²/an.",
                [
                    "Vérifier la surface de référence.",
                    "Contrôler les factures sur 12 mois.",
                    "Vérifier les usages inclus dans les compteurs."
                ],
                [
                    "Réaliser une analyse détaillée des consommations.",
                    "Identifier les postes énergétiques dominants."
                ],
                "Moyenne"
            )
        elif intensity >= 250:
            add(
                "Énergie",
                "Intensité énergétique à investiguer",
                "Modérée",
                "Consommation à comparer à des bâtiments équivalents.",
                f"Intensité déclarée : {intensity:.1f} kWh/m²/an.",
                [
                    "Vérifier le périmètre des consommations.",
                    "Comparer les usages et horaires d'occupation."
                ],
                [
                    "Mettre en place un suivi énergétique.",
                    "Rechercher les principaux postes consommateurs."
                ],
                "Moyenne"
            )

    # 2. Chauffage
    heating = number("heating_setpoint_c")

    if heating is not None and heating > 20:
        add(
            "Chauffage",
            "Consigne de chauffage élevée",
            "Modérée",
            "Régulation potentiellement inadaptée à l'occupation.",
            f"Consigne renseignée : {heating:.1f} °C.",
            [
                "Vérifier les températures réelles.",
                "Contrôler la programmation et les zones."
            ],
            [
                "Adapter les consignes au confort requis.",
                "Optimiser la programmation horaire."
            ],
            "Élevée"
        )

    # 3. Refroidissement
    cooling = number("cooling_setpoint_c")

    if data.get("has_cooling") and cooling is not None and cooling < 24:
        add(
            "Climatisation",
            "Consigne de refroidissement basse",
            "Modérée",
            "Consigne potentiellement énergivore.",
            f"Consigne renseignée : {cooling:.1f} °C.",
            [
                "Vérifier le confort des occupants.",
                "Contrôler les horaires de fonctionnement."
            ],
            [
                "Étudier une adaptation des consignes.",
                "Optimiser les plages de fonctionnement."
            ],
            "Élevée"
        )

    # 4. Chauffage et climatisation
    if (
        data.get("has_cooling")
        and heating is not None
        and cooling is not None
        and heating > cooling
    ):
        add(
            "Régulation CVC",
            "Risque de conflit entre consignes",
            "Élevée",
            "Les consignes pourraient favoriser des demandes opposées.",
            f"Chauffage : {heating} °C ; froid : {cooling} °C.",
            [
                "Contrôler les séquences de régulation.",
                "Analyser les historiques de fonctionnement."
            ],
            [
                "Vérifier les bandes neutres.",
                "Éviter les demandes simultanées."
            ],
            "Moyenne"
        )

    # 5. Ventilation
    ventilation_hours = number("ventilation_schedule_hours_day")
    occupancy_week = number("occupancy_hours_week")

    if (
        data.get("has_ventilation")
        and ventilation_hours is not None
        and ventilation_hours > 18
        and occupancy_week is not None
        and occupancy_week <= 50
    ):
        add(
            "Ventilation",
            "Horaires de ventilation à vérifier",
            "Modérée",
            "Fonctionnement potentiellement prolongé hors occupation.",
            f"Ventilation : {ventilation_hours} h/j ; "
            f"occupation : {occupancy_week} h/semaine.",
            [
                "Contrôler les calendriers de ventilation.",
                "Vérifier les besoins hors occupation."
            ],
            [
                "Adapter les horaires si les exigences le permettent.",
                "Étudier une régulation selon l'occupation."
            ],
            "Moyenne"
        )

    # 6. Éclairage
    lighting_hours = number("lighting_schedule_hours_day")

    if (
        data.get("has_lighting")
        and lighting_hours is not None
        and lighting_hours > 12
    ):
        add(
            "Éclairage",
            "Durée d'éclairage importante",
            "Modérée",
            "Éclairage potentiellement maintenu hors occupation.",
            f"Durée renseignée : {lighting_hours} h/j.",
            [
                "Vérifier les horaires réels.",
                "Contrôler les détecteurs de présence."
            ],
            [
                "Adapter les plages horaires.",
                "Étudier la détection et la gradation."
            ],
            "Moyenne"
        )

    # 7. Qualité des données
    if not data.get("meter_separation"):
        add(
            "Instrumentation",
            "Sous-comptage insuffisant",
            "Information",
            "Les consommations par usage ne sont pas isolées.",
            "Absence de séparation des compteurs déclarée.",
            [
                "Inventorier les compteurs existants.",
                "Identifier les usages non mesurés."
            ],
            [
                "Étudier un plan de sous-comptage.",
                "Suivre les consommations par énergie."
            ],
            "Élevée"
        )

    return diagnostics

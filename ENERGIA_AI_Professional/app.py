from __future__ import annotations

import streamlit as st
import pandas as pd

from engine import (analyse_building, build_recommendations, ask_ai,
                             diagnose_building, estimate_savings, estimate_carbon)
from geodata import geocode_address, search_tertiary_dpe
from building_enrichment import locate, enrich
from services.prefill import approved_prefill
from report_pdf import generate_report

st.set_page_config(
    page_title="HVAC AI Advisor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit-native light theme is configured in .streamlit/config.toml.
st.markdown("""
<style>
:root { color-scheme: light; }
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #f4f7fb !important;
    color: #172b4d !important;
}
[data-testid="stHeader"] { background: rgba(255,255,255,.96) !important; }
[data-testid="stSidebar"] {
    background: #10243a !important;
    border-right: 1px solid #203b57;
}
[data-testid="stSidebar"] * { color: #eaf2fb !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 8px 10px; border-radius: 8px;
}
.block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
h1,h2,h3,h4,h5,h6 { color: #172b4d !important; letter-spacing: -.02em; }
p, li, label, [data-testid="stMarkdownContainer"] { color: #344563; }
.hero {
    background: linear-gradient(115deg,#102a43 0%,#164e63 100%);
    padding: 30px 34px; border-radius: 18px; margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(16,42,67,.12);
}
.hero h1 { color: #ffffff !important; font-size: 2.15rem; margin: 0 0 8px 0; }
.hero p { color: #d9e8f4 !important; font-size: 1.02rem; margin: 0; }
.eyebrow { color: #70d6d0 !important; font-size: .76rem; font-weight: 700;
    letter-spacing: .12em; text-transform: uppercase; margin-bottom: 8px; }
.section-note { color: #62748a; font-size: .92rem; margin-top: -8px; }
div[data-testid="stMetric"] {
    background: #ffffff !important; border: 1px solid #e3eaf2 !important;
    border-radius: 14px; padding: 18px 20px; box-shadow: 0 3px 12px rgba(16,42,67,.045);
}
[data-testid="stMetricLabel"] { color: #62748a !important; }
[data-testid="stMetricValue"] { color: #102a43 !important; font-weight: 700; }
div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff; border: 1px solid #e3eaf2; border-radius: 14px;
    padding: 18px; box-shadow: 0 3px 12px rgba(16,42,67,.035);
}
.stButton > button, .stFormSubmitButton > button {
    background: #087e8b !important; color: #ffffff !important;
    border: 1px solid #087e8b !important; border-radius: 9px;
    font-weight: 600; min-height: 42px;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #066873 !important; border-color: #066873 !important;
}
input, textarea, [data-baseweb="select"] > div {
    background: #ffffff !important; color: #172b4d !important;
    border-color: #cbd6e2 !important;
}
[data-testid="stAlert"] { border-radius: 10px; }
div[data-testid="stDataFrame"] { border: 1px solid #e3eaf2; border-radius: 10px; }
hr { border-color: #e3eaf2; }
.small-muted { color: #718096; font-size: .82rem; }
.kpi-label { color: #718096; font-size: .82rem; }
</style>
""", unsafe_allow_html=True)

if "building" not in st.session_state:
    st.session_state.building = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "dpe_candidates" not in st.session_state:
    st.session_state.dpe_candidates = []

with st.sidebar:
    st.markdown("## ⚡ HVAC AI")
    st.caption("BUILDING ENERGY INTELLIGENCE")
    st.divider()
    page = st.radio(
        "ESPACE DE TRAVAIL",
        ["Vue d'ensemble", "Bâtiment", "Audit énergétique", "AI Advisor", "Rapports & méthode"],
        label_visibility="visible",
    )
    st.divider()
    if st.session_state.building:
        st.markdown("**Bâtiment actif**")
        st.caption(st.session_state.building.get("address", "Adresse enregistrée"))
    else:
        st.caption("Aucun bâtiment sélectionné")
    st.markdown("---")
    st.caption("Prototype d'aide à la décision · Version démonstrateur")

st.markdown("""
<div class="hero">
  <div class="eyebrow">ENERGY & HVAC INTELLIGENCE</div>
  <h1>HVAC AI Advisor</h1>
  <p>Comprendre la performance de vos bâtiments, identifier les leviers d'action et comparer les solutions CVC.</p>
</div>
""", unsafe_allow_html=True)

def fmt_num(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")

if page == "Vue d'ensemble":
    st.title("Vue d'ensemble")
    st.markdown('<p class="section-note">Synthèse de votre bâtiment et accès rapide aux principaux modules.</p>', unsafe_allow_html=True)
    building = st.session_state.building
    analysis = st.session_state.analysis

    if building:
        st.success(f"Bâtiment sélectionné · {building.get('address', '')}")
    else:
        st.info("Commencez par enregistrer un bâtiment dans le module « Bâtiment ».")

    if analysis:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Consommation annuelle", f"{fmt_num(analysis['total_kwh'])} kWh")
        c2.metric("Intensité énergétique", f"{fmt_num(analysis['intensity'], 1)} kWh/m²/an")
        c3.metric("Dépenses annuelles", f"{fmt_num(analysis['annual_cost'])} €")
        c4.metric("Prix moyen déclaré", f"{fmt_num(analysis['price_per_kwh'], 3)} €/kWh")
        st.subheader("Répartition des consommations")
        energy_df = pd.DataFrame({
            "Énergie": ["Électricité", "Gaz", "Réseau de chaleur"],
            "Consommation (kWh)": [analysis["electricity"], analysis["gas"], analysis["district"]],
        })
        energy_df = energy_df[energy_df["Consommation (kWh)"] > 0]
        if not energy_df.empty:
            st.bar_chart(energy_df.set_index("Énergie"))
        else:
            st.caption("Aucune consommation n'a été saisie.")
    else:
        a, b = st.columns(2)
        with a:
            st.markdown("### 01 · Identifier")
            st.write("Localisez un bâtiment à partir de son adresse et conservez ses informations dans cette session.")
            if st.button("Ouvrir le module bâtiment", use_container_width=True):
                st.session_state["nav_target"] = "Bâtiment"
                st.rerun()
        with b:
            st.markdown("### 02 · Analyser")
            st.write("Saisissez les consommations et dépenses pour calculer les premiers indicateurs énergétiques.")
            if st.button("Ouvrir l'audit énergétique", use_container_width=True):
                st.session_state["nav_target"] = "Audit énergétique"
                st.rerun()
        st.caption("Les données affichées dans cette application sont celles que vous saisissez ou celles explicitement identifiées comme provenant d'une source publique.")

elif page == "Bâtiment":
    st.title("Identification automatique du bâtiment")
    st.caption("Géoplateforme, DPE ADEME et connecteur BDNB optionnel. Confirmez toujours le périmètre audité.")
    address = st.text_input("Adresse complète", placeholder="10 rue de la Paix, 75002 Paris")
    if st.button("Rechercher l'adresse", type="primary"):
        if not address.strip():
            st.warning("Saisissez une adresse.")
        else:
            try:
                st.session_state.address_candidates = locate(address.strip())
                st.session_state.enrichment = None
                st.session_state.building = None
                if not st.session_state.address_candidates:st.warning("Adresse non trouvée.")
            except Exception as exc:
                st.error(f"Géocodage indisponible : {type(exc).__name__}. Réessayez plus tard.")
    candidates=st.session_state.get('address_candidates',[])
    if candidates:
        idx=st.selectbox("Sélectionner l'adresse exacte",range(len(candidates)),format_func=lambda i:candidates[i]['address'])
        if st.button("Identifier les bâtiments et rechercher les DPE"):
            st.session_state.building=candidates[idx]
            with st.spinner("Recherche des données publiques…"):
                st.session_state.enrichment=enrich(candidates[idx])
    if st.session_state.get('building'):
        b=st.session_state.building
        st.write('**Adresse retenue :**',b['address'])
        st.caption('Coordonnées de l’adresse, pas nécessairement du centre du bâtiment.')
    enriched=st.session_state.get('enrichment')
    if enriched:
        for warning in enriched['warnings']:st.warning(warning)
        st.subheader('DPE candidats — vérification obligatoire')
        dpes=enriched['dpe']
        if dpes:
            import pandas as pd
            st.dataframe(pd.DataFrame([{k:v for k,v in item.items() if k in ('id','kind','address','address_match','surface_m2','construction_year','heating_type','energy_class','ghg_class')} for item in dpes]),use_container_width=True)
            selected=st.selectbox('Choisir le diagnostic correspondant au bien audité',range(len(dpes)),format_func=lambda i:f"{dpes[i]['kind']} | {dpes[i]['address']} | DPE {dpes[i]['id']}")
            item=dpes[selected]
            st.warning(item['warning'])
            confirmed=st.checkbox('Je confirme que ce DPE concerne précisément le logement, local ou bâtiment que je vais auditer.',key='confirm_dpe')
            if st.button('Préremplir la fiche depuis ce DPE',disabled=not confirmed):
                st.session_state.prefill=approved_prefill(item)
                if st.session_state.prefill.get('surface_m2'):
                    st.session_state.audit_surface=float(st.session_state.prefill['surface_m2'])
                st.session_state.prefill_source=item['source']
                for field, key in [('construction_year','audit_year'), ('heating_type','audit_heating'), ('ventilation_type','audit_ventilation'), ('dhw_type','audit_dhw'), ('cooling_type','audit_cooling'), ('building_use','audit_usage')]:
                    if st.session_state.prefill.get(field) not in (None, ''):
                        st.session_state[key] = str(st.session_state.prefill[field])
                st.success('Fiche enrichie. Ouvrez Audit énergétique pour vérifier les champs préremplis.')
        else:st.info('Aucun DPE candidat trouvé. La saisie manuelle reste disponible.')
        if enriched['bdnb']:
            st.subheader('Résultats BDNB bruts (à contrôler)')
            st.json(enriched['bdnb'][:5])
        st.caption('L’absence de DPE ne signifie pas que le bâtiment n’existe pas. Aucun résultat ne constitue une identification certaine sans validation.')

elif page == "Audit énergétique":
    st.title("Audit énergétique simplifié")
    st.markdown('<p class="section-note">Calcul des consommations, de l’intensité énergétique et du coût moyen à partir des données déclarées.</p>', unsafe_allow_html=True)
    if st.session_state.building:
        st.info(f"Bâtiment concerné : {st.session_state.building['address']}")
    with st.form("energy_form"):
        st.subheader("Caractéristiques et consommations")
        c1, c2 = st.columns(2)
        with c1:
            prefill = st.session_state.get('prefill', {})
            surface = st.number_input("Surface utile (m²) — confirmer la nature de la surface", min_value=1.0, value=float(prefill.get('surface_m2') or 500.0), step=10.0, key='audit_surface')
            if prefill.get('surface_m2'):
                st.caption('Surface importée d’un DPE sélectionné : vérifier qu’elle correspond à la surface utile du périmètre audité.')
            st.text_input("Usage du bâtiment (à confirmer)", key="audit_usage", placeholder="bureaux, résidentiel, école…")
            st.text_input("Année / période de construction", key="audit_year")
            st.text_input("Système / énergie de chauffage", key="audit_heating")
            st.text_input("Type de ventilation", key="audit_ventilation")
            st.text_input("Production ECS", key="audit_dhw")
            st.text_input("Climatisation / refroidissement", key="audit_cooling")
            with st.expander("Données d'enveloppe et DPE récupérées"):
                for field,label in [('wall_insulation','Isolation des murs'),('roof_insulation','Isolation toiture'),('glazing','Vitrage'),('energy_class','Classe énergie'),('ghg_class','Classe GES')]:
                    st.text_input(label, value=str(prefill.get(field) or ''), disabled=True)
                st.caption("Champs DPE informatifs, non assimilés à des mesures actuelles.")
            electricity = st.number_input("Électricité (kWh/an)", min_value=0.0, value=0.0, step=1000.0)
            annual_cost = st.number_input("Dépenses énergétiques (€ / an)", min_value=0.0, value=0.0, step=500.0)
        with c2:
            gas = st.number_input("Gaz (kWh/an)", min_value=0.0, value=0.0, step=1000.0)
            district = st.number_input("Réseau de chaleur (kWh/an)", min_value=0.0, value=0.0, step=1000.0)
            st.caption("Saisissez des consommations sur une période de 12 mois cohérente.")
        submitted = st.form_submit_button("Calculer les indicateurs", type="primary", use_container_width=True)
    if submitted:
        st.session_state.analysis = analyse_building(
            surface, electricity, gas, district, annual_cost,
            building_type=st.session_state.get('audit_usage') or 'unknown',
            construction_year=int(st.session_state['audit_year']) if str(st.session_state.get('audit_year','')).isdigit() else None,
            heating_type=st.session_state.get('audit_heating') or 'unknown',
            cooling_type=st.session_state.get('audit_cooling') or 'unknown',
            ventilation_type=st.session_state.get('audit_ventilation') or 'unknown',
            dhw_type=st.session_state.get('audit_dhw') or 'unknown',
            address=(st.session_state.get('building') or {}).get('address',''),
        )
        st.session_state.analysis['prefill_source'] = st.session_state.get('prefill_source')
    result = st.session_state.analysis
    if result:
        st.divider()
        st.subheader("Résultats")
        a, b, c = st.columns(3)
        a.metric("Consommation totale", f"{fmt_num(result['total_kwh'])} kWh/an")
        b.metric("Intensité énergétique", f"{fmt_num(result['intensity'], 1)} kWh/m²/an")
        c.metric("Coût moyen", f"{fmt_num(result['price_per_kwh'], 3)} €/kWh")
        chart = pd.DataFrame({
            "Énergie": ["Électricité", "Gaz", "Réseau de chaleur"],
            "kWh/an": [result["electricity"], result["gas"], result["district"]],
        }).set_index("Énergie")
        st.bar_chart(chart)
        st.caption("Calculs établis à partir des données saisies. Ils ne constituent ni un DPE ni un audit réglementaire.")

elif page == "AI Advisor":
    st.title("AI Energy Advisor")
    st.markdown('<p class="section-note">Recommandations préliminaires fondées sur les indicateurs calculés et les règles métier du prototype.</p>', unsafe_allow_html=True)
    result = st.session_state.analysis
    if not result:
        st.info("Réalisez d'abord une analyse énergétique pour activer le conseiller.")
    else:
        recs = build_recommendations(result)
        diagnosis = diagnose_building(result)
        savings = estimate_savings(result, recs)
        carbon = estimate_carbon(result)

        st.subheader("Synthèse du diagnostic")
        st.caption(diagnosis["confidence"])
        if diagnosis["alerts"]:
            for alert in diagnosis["alerts"]:
                if alert["level"] == "À investiguer":
                    st.error(f"**{alert['title']}** — {alert['detail']}")
                else:
                    st.warning(f"**{alert['title']}** — {alert['detail']}")
        else:
            st.success("Aucune alerte de screening détectée avec les données actuellement saisies.")
        for observation in diagnosis["observations"]:
            st.write(f"• {observation}")

        # DIAGNOSTIC TECHNIQUE DETAILLE
        st.divider()
        st.subheader("Diagnostic technique détaillé")

        detailed = diagnosis.get("detailed_diagnostics", [])

        if detailed:
            st.caption(
                f"{len(detailed)} constat(s) technique(s) "
                "identifié(s) par le moteur expert."
            )

            for idx, diagnostic in enumerate(detailed, start=1):

                title = diagnostic.get("title", "Diagnostic")
                severity = diagnostic.get("severity", "À vérifier")
                category = diagnostic.get("category", "Général")

                with st.expander(
                    f"{idx:02d} · {category} — {title} "
                    f"[{severity}]",
                    expanded=(idx == 1)
                ):
                    st.markdown("**Cause possible**")
                    st.write(
                        diagnostic.get("cause", "Non déterminée")
                    )

                    st.markdown("**Éléments du diagnostic**")
                    st.info(
                        diagnostic.get("evidence", "Non renseignés")
                    )

                    st.markdown("**Contrôles techniques**")
                    for check in diagnostic.get("checks", []):
                        st.write(f"• {check}")

                    st.markdown("**Actions recommandées**")
                    for action in diagnostic.get("actions", []):
                        st.write(f"• {action}")

                    st.caption(
                        "Confiance : "
                        + diagnostic.get("confidence", "À qualifier")
                    )
        else:
            st.info(
                "Aucun diagnostic technique détaillé "
                "déclenché avec les données disponibles."
            )

        st.subheader("Indicateurs complémentaires")
        m1, m2, m3 = st.columns(3)
        m1.metric("Émissions estimées", f"{fmt_num(carbon['total_tonnes'], 2)} tCO₂e/an")
        m2.metric("Économies d'énergie potentielles", f"{fmt_num(savings['low_kwh'])}–{fmt_num(savings['high_kwh'])} kWh/an")
        m3.metric("Économies financières potentielles", f"{fmt_num(savings['low_eur'])}–{fmt_num(savings['high_eur'])} €/an")
        st.caption(savings.get("warning", ""))
        st.caption(carbon["warning"])

        st.divider()
        st.subheader("Plan d'actions préliminaire")
        if not recs:
            st.info("Renseignez des consommations annuelles pour générer des pistes d'action.")
        for idx, item in enumerate(recs, start=1):
            with st.container(border=True):
                c1, c2 = st.columns([4, 2])
                c1.markdown(f"**{idx:02d} · {item['title']}**")
                c1.write(item["detail"])
                c2.markdown("**Priorité**")
                c2.markdown("**Priorité**")
                c2.write(item["priority"])
                st.caption(f"Catégorie : {item['category']} · Fondement : {item['basis']}")
                st.caption(f"Fourchette indicative : {item['savings_low_pct']} à {item['savings_high_pct']} % — non garantie et non cumulable.")
                with st.expander("Vérifications techniques à effectuer"):
                    for check in item["checks"]:
                        st.write(f"• {check}")
        st.divider()
        st.subheader("Interroger le conseiller")
        question = st.text_area("Votre question", placeholder="Quelles vérifications effectuer avant d'envisager une pompe à chaleur ?")
        if st.button("Générer une réponse", type="primary", disabled=not question.strip()):
            with st.spinner("Préparation de la réponse…"):
                answer, mode = ask_ai(question, result, recs)
            st.markdown(answer)
            st.caption(f"Mode : {mode}")

elif page == "Rapports & méthode":
    st.title("Rapports & méthode")
    st.markdown('<p class="section-note">Transparence sur les données, les calculs et les limites du démonstrateur.</p>', unsafe_allow_html=True)
    if st.session_state.analysis:
        data = st.session_state.analysis
        report = pd.DataFrame([{
            "Surface (m²)": data["surface"],
            "Électricité (kWh/an)": data["electricity"],
            "Gaz (kWh/an)": data["gas"],
            "Réseau chaleur (kWh/an)": data["district"],
            "Total (kWh/an)": data["total_kwh"],
            "Intensité (kWh/m²/an)": data["intensity"],
            "Dépenses (€ / an)": data["annual_cost"],
        }])
        st.subheader("Exporter les indicateurs")
        try:
            diag = diagnose_building(data)
            recs = build_recommendations(data)
            pdf = generate_report(data, diag, recs, estimate_carbon(data),
                                  estimate_savings(data, recs),
                                  st.session_state.get('building'),
                                  st.session_state.get('prefill'))
            st.download_button("📄 Télécharger le rapport PDF", data=pdf,
                               file_name="HVAC_Building_Rapport_Energetique.pdf",
                               mime="application/pdf", use_container_width=True)
        except Exception as exc:
            st.error(f"Génération PDF impossible : {type(exc).__name__} — {exc}")
        st.download_button(
            "Télécharger les résultats au format CSV",
            data=report.to_csv(index=False).encode("utf-8-sig"),
            file_name="hvac_ai_advisor_analyse.csv",
            mime="text/csv",
        )
        st.dataframe(report, use_container_width=True)
    st.divider()
    st.subheader("Origine et fiabilité des données")
    st.markdown("""
    - **Adresse et coordonnées :** géocodage public ; elles ne donnent pas accès aux consommations réelles.
    - **Consommations et coûts :** données déclarées par l'utilisateur dans ce prototype.
    - **DPE :** la recherche de candidats est indicative et doit être vérifiée sur le bâtiment exact.
    - **Recommandations :** règles métier préliminaires ; elles ne remplacent pas une étude thermique.
    - **Enedis / GRDF :** les données réelles nécessitent les autorisations, contrats et accès appropriés.
    """)
    st.warning("Cet outil est un démonstrateur d'aide à la décision. Il ne remplace pas un DPE, un audit réglementaire, un calcul de dimensionnement ni la validation d'un ingénieur.")

# Keep navigation state simple and deterministic after button click.
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    st.info(f"Pour ouvrir « {target} », sélectionnez ce module dans le menu latéral.")

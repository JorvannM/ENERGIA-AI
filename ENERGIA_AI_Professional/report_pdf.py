"""Rapport PDF de pré-diagnostic; aucun chiffre conventionnel DPE présenté comme réel."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4


def generate_report(data, diagnosis, recommendations, carbon, savings, building=None, prefill=None):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=48, bottomMargin=45)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitleHVAC", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#15344a")))
    styles.add(ParagraphStyle(name="SmallHVAC", parent=styles["BodyText"], fontSize=8.5, leading=12, spaceAfter=5))
    story = [Paragraph("ENERGIA AI — PRÉ-DIAGNOSTIC ÉNERGÉTIQUE", styles["ReportTitleHVAC"]), Spacer(1, 10)]
    def para(s, style="SmallHVAC"):
        return Paragraph(escape(str(s)), styles[style])
    address = (building or {}).get("address") or data.get("address") or "Non renseignée"
    story.extend([para("Bâtiment : " + str((building or {}).get("name") or "Non renseigné")), para("Adresse : " + str(address)), para("Document d'aide à la décision — ni audit réglementaire ni DPE."), Spacer(1, 10)])
    def fmt(v, digits=1):
        try: return f"{float(v):,.{digits}f}".replace(",", " ")
        except (TypeError, ValueError): return "Non renseigné"
    metrics = [
        ("Surface déclarée / validée", fmt(data.get("surface_m2")) + " m²"),
        ("Électricité", fmt(data.get("electricity_kwh"),0) + " kWh/an"),
        ("Gaz", fmt(data.get("gas_kwh"),0) + " kWh/an"),
        ("Réseau de chaleur", fmt(data.get("district_kwh"),0) + " kWh/an"),
        ("Total", fmt(data.get("total_kwh"),0) + " kWh/an"),
        ("Intensité", fmt(data.get("intensity")) + " kWh/m²/an"),
        ("Dépenses", fmt(data.get("annual_cost"),0) + " EUR/an"),
        ("Émissions indicatives", fmt(carbon.get("total_tonnes"),2) + " tCO2e/an"),
    ]
    story.append(para("INDICATEURS", "Heading2"))
    t=Table([[para(a),para(b)] for a,b in metrics],colWidths=[230,260],hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f5f8")),("BOTTOMPADDING",(0,0),(-1,-1),7), ("TOPPADDING",(0,0),(-1,-1),7), ("LINEBELOW",(0,0),(-1,-2),0.4,colors.HexColor("#d5e0e6"))]))
    story.extend([t,Spacer(1,12),para("CARACTÉRISTIQUES DU BÂTIMENT", "Heading2")])
    for key,label in [("building_type","Usage"),("construction_year","Construction"),("heating_type","Chauffage"),("cooling_type","Climatisation"),("ventilation_type","Ventilation"),("lighting_type","Éclairage"),("dhw_type","ECS")]:
        story.append(para(f"{label} : {data.get(key) or 'Non renseigné'}"))
    if prefill:
        story.append(para(f"Source des caractéristiques préremplies : {prefill.get('source','Non renseignée')} ; DPE {prefill.get('dpe_id','non précisé')}"))
        story.append(para(prefill.get("scope_warning", "Vérifier la correspondance avec le bâtiment audité.")))
    story.extend([Spacer(1,8),para("ALERTES ET POINTS DE CONTRÔLE", "Heading2")])
    alerts=diagnosis.get("alerts",[])
    if not alerts: story.append(para("Aucune alerte détectée sur les données renseignées ; cela ne prouve pas l'absence de défaut."))
    for a in alerts[:25]:
        story.append(para(f"[{a.get('level','À vérifier')}] {a.get('title','Contrôle')} — {a.get('detail','')}"))
    story.extend([Spacer(1,8),para("PLAN D'ACTIONS INDICATIF", "Heading2")])
    for i,r in enumerate(recommendations[:24],1):
        story.append(para(f"{i}. {r.get('title','Action')} ({r.get('category','')}) — {r.get('detail','')}"))
    story.extend([Spacer(1,10),para("ÉCONOMIES POTENTIELLES", "Heading2")])
    story.append(para("Fourchette indicative : " + fmt(savings.get("low_kwh"),0) + " à " + fmt(savings.get("high_kwh"),0) + " kWh/an"))
    story.extend([Spacer(1,10),para("LIMITES ET HYPOTHÈSES", "Heading2")])
    story.append(para(diagnosis.get("confidence","Pré-diagnostic fondé sur des données déclarées.")))
    story.append(para(savings.get("warning","Les économies ne sont pas garanties.")))
    story.append(para(carbon.get("warning","Facteurs d'émission indicatifs.")))
    story.append(para("Consommations issues des saisies utilisateur ; les consommations conventionnelles DPE ne sont pas des consommations facturées. Les recommandations nécessitent une validation technique."))
    def footer(canvas, doc):
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(42,25,"ENERGIA AI — rapport indicatif")
        canvas.drawRightString(A4[0]-42,25,f"Page {doc.page}")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

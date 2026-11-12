"""Interface HTTP additionnelle : le moteur V5 original n'est pas modifié."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from engine import analyse_building, diagnose_building, build_recommendations, estimate_savings, estimate_carbon, ask_ai
from report_pdf import generate_report

ROOT = Path(__file__).parent
app = FastAPI(title='ENERGIA AI | Building Intelligence', docs_url='/api/docs')
app.mount('/static', StaticFiles(directory=ROOT/'web'/'static'), name='static')
class AuditInput(BaseModel):
    surface: float = Field(gt=0)
    electricity: float = Field(ge=0)
    gas: float = Field(ge=0)
    district: float = Field(ge=0)
    annual_cost: float = Field(ge=0)
    name: str = ''
    address: str = ''
    building_type: str = 'bureaux'
    heating_type: str = 'unknown'
    cooling_type: str = 'unknown'
    ventilation_type: str = 'unknown'
    lighting_type: str = 'unknown'
    dhw_type: str = 'unknown'
    meter_separation: bool = False
    occupancy_hours_week: float = 50
    construction_year: int | None = None

class QuestionInput(BaseModel):
    audit: AuditInput
    question: str = Field(min_length=1, max_length=2000)

def calculate(payload: AuditInput):
    try:
        data = analyse_building(**payload.model_dump())
        diagnosis = diagnose_building(data)
        recommendations = build_recommendations(data)
        savings = estimate_savings(data, recommendations)
        carbon = estimate_carbon(data)
        return dict(data=data, diagnosis=diagnosis, recommendations=recommendations, savings=savings, carbon=carbon)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc

@app.get('/')
def home():
    return FileResponse(ROOT/'web'/'index.html')

@app.post('/api/analyze')
def analyze(payload: AuditInput):
    return calculate(payload)

@app.post('/api/ask')
def ask(payload: QuestionInput):
    result = calculate(payload.audit)
    answer, mode = ask_ai(payload.question, result['data'], result['recommendations'])
    return {'answer': answer, 'mode': mode}

@app.post('/api/report')
def report(payload: AuditInput):
    result = calculate(payload)
    try:
        output = generate_report(result['data'], result['diagnosis'], result['recommendations'], result['carbon'], result['savings'], building=payload.model_dump())
        if hasattr(output, 'getvalue'): output = output.getvalue()
        if isinstance(output, (bytes, bytearray)):
            return Response(content=output, media_type='application/pdf', headers={'Content-Disposition':'attachment; filename="ENERGIA_AI_Rapport.pdf"'})
        raise ValueError('Format de rapport inattendu')
    except Exception as exc:
        raise HTTPException(500, detail=f'Génération du rapport impossible : {exc}') from exc


# Identification publique : les données DPE ne sont jamais assimilées à des factures.
from building_enrichment import locate, enrich
from services.prefill import approved_prefill

class AddressQuery(BaseModel):
    address: str = Field(min_length=5, max_length=300)

class LocationQuery(BaseModel):
    location: dict

class PrefillQuery(BaseModel):
    candidate: dict

@app.post('/api/address/search')
def address_search(payload: AddressQuery):
    try:
        return {'locations': locate(payload.address)}
    except Exception as exc:
        raise HTTPException(503, detail='Service de géocodage indisponible : '+str(exc)) from exc

@app.post('/api/address/dpe')
def address_dpe(payload: LocationQuery):
    if not payload.location.get('address'):
        raise HTTPException(422, detail='Adresse sélectionnée manquante')
    return enrich(payload.location)

@app.post('/api/address/prefill')
def address_prefill(payload: PrefillQuery):
    return approved_prefill(payload.candidate)

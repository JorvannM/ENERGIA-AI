"""Interface HTTP additionnelle : le moteur V5 original n'est pas modifié."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, Response, JSONResponse
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
    lighting_fixture_count: int | None = Field(default=None, gt=0)
    lighting_power_existing_w: float | None = Field(default=None, gt=0)
    lighting_power_proposed_w: float | None = Field(default=None, gt=0)
    lighting_schedule_hours_day: float | None = Field(default=None, gt=0, le=24)
    electricity_price_eur_kwh: float | None = Field(default=None, ge=0)
    lighting_investment_eur: float | None = Field(default=None, ge=0)
    cooling_capacity_kw: float | None = Field(default=None, gt=0)
    cooling_hours_year: float | None = Field(default=None, ge=0, le=8760)
    cooling_eer_existing: float | None = Field(default=None, gt=0)
    cooling_eer_proposed: float | None = Field(default=None, gt=0)
    heating_energy_kwh_year: float | None = Field(default=None, ge=0)
    heating_reduction_pct: float | None = Field(default=None, ge=0, le=100)
    ventilation_fan_power_w: float | None = Field(default=None, gt=0)
    ventilation_schedule_hours_day: float | None = Field(default=None, ge=0, le=24)
    ventilation_proposed_hours_day: float | None = Field(default=None, ge=0, le=24)

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

# V8 Lot 1: local portfolio prototype (no authentication; local-only).
from enterprise.store import init_db, Session, User, save_building, list_buildings, get_building, save_audit, list_audits, get_audit
from enterprise.auth import get_user, csrf_token, require_write, signer, COOKIE, SESSION_SECONDS, PH
from sqlalchemy import select
from argon2.exceptions import VerifyMismatchError, VerificationError
import os

init_db()

class LoginInput(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=1,max_length=200)

@app.post('/api/auth/login')
def login(payload:LoginInput,request:Request):
    with Session() as db:
        account=db.scalar(select(User).where(User.email==payload.email.strip().lower()))
        try: valid=bool(account) and PH.verify(account.password_hash,payload.password)
        except (VerifyMismatchError,VerificationError):valid=False
        if not valid:raise HTTPException(401,'Identifiants invalides')
        uid,org=account.id,account.organization_id
    secure=os.getenv('ENERGIA_SECURE_COOKIES','0')=='1'
    resp=JSONResponse({'ok':True})
    resp.set_cookie(COOKIE,signer().dumps({'uid':uid,'org':org}),httponly=True,secure=secure,samesite='strict',max_age=SESSION_SECONDS,path='/')
    return resp

@app.get('/api/auth/me')
def me(request:Request):
    user=get_user(request)
    return {'user':user,'csrf':csrf_token(request)}

@app.post('/api/auth/logout')
def logout():
    response=JSONResponse({'ok':True})
    response.delete_cookie(COOKIE,path='/')
    return response

@app.middleware('http')
async def protect_api(request:Request,call_next):
    path=request.url.path
    if path.startswith('/api/') and path not in ('/api/auth/login','/api/auth/me'):
        try:
            get_user(request)
            if request.method not in ('GET','HEAD','OPTIONS'):
                from enterprise.auth import verify_csrf
                verify_csrf(request)
        except HTTPException as exc:
            return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
    if path.startswith('/api/docs') or path.startswith('/openapi.json'):
        try:get_user(request)
        except HTTPException as exc:return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
    return await call_next(request)


@app.get('/api/v8/buildings')
def v8_buildings(user=Depends(get_user)):
    return {'buildings':list_buildings(user["organization_id"])}

@app.post('/api/v8/buildings',status_code=201)
def v8_create_building(payload: AuditInput,user=Depends(get_user)):
    require_write(user)
    return {'id':save_building(user["organization_id"],payload.model_dump())}

@app.get('/api/v8/buildings/{building_id}')
def v8_get_building(building_id: str,user=Depends(get_user)):
    result=get_building(user["organization_id"],building_id)
    if not result:raise HTTPException(404,'Bâtiment introuvable')
    return result

@app.post('/api/v8/buildings/{building_id}/audits',status_code=201)
def v8_create_audit(building_id: str,payload: AuditInput,user=Depends(get_user)):
    require_write(user)
    if not get_building(user["organization_id"],building_id):raise HTTPException(404,'Bâtiment introuvable')
    result=calculate(payload)
    audit_id=save_audit(user["organization_id"],user["id"],building_id,payload.model_dump(),result)
    return {'id':audit_id,'result':result}

@app.get('/api/v8/buildings/{building_id}/audits')
def v8_audits(building_id: str,user=Depends(get_user)):
    if not get_building(user["organization_id"],building_id):raise HTTPException(404,'Bâtiment introuvable')
    return {'audits':list_audits(user["organization_id"],building_id)}

@app.get('/api/v8/buildings/{building_id}/audits/{audit_id}')
def v8_get_audit(building_id: str,audit_id: str,user=Depends(get_user)):
    result=get_audit(user["organization_id"],building_id,audit_id)
    if not result:raise HTTPException(404,'Audit introuvable')
    return result

# V8 Lot 2 : administration des collaborateurs (sans modification du moteur V5).
from enterprise.admin import router as enterprise_admin_router
app.include_router(enterprise_admin_router)

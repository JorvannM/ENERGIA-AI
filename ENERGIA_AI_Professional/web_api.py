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
    gas_price_eur_kwh: float | None = Field(default=None, ge=0)
    heating_investment_eur: float | None = Field(default=None, ge=0)
    ventilation_investment_eur: float | None = Field(default=None, ge=0)
    cooling_investment_eur: float | None = Field(default=None, ge=0)
    heating_energy_price_eur_kwh: float | None = Field(default=None, ge=0)
    district_price_eur_kwh: float | None = Field(default=None, ge=0)
    ventilation_fan_power_w: float | None = Field(default=None, gt=0)
    ventilation_schedule_hours_day: float | None = Field(default=None, ge=0, le=24)
    ventilation_proposed_hours_day: float | None = Field(default=None, ge=0, le=24)

class QuestionInput(BaseModel):
    audit: AuditInput
    question: str = Field(min_length=1, max_length=2000)
    allow_external_ai: bool = False

def calculate(payload: AuditInput):
    try:
        data = analyse_building(**payload.model_dump())
        diagnosis = diagnose_building(data)
        recommendations = build_recommendations(data)
        savings = estimate_savings(data, recommendations)
        carbon = estimate_carbon(data)
        from energy_breakdown import build_energy_breakdown
        energy_breakdown = build_energy_breakdown(data)
        from energy_intelligence import analyze_energy_breakdown
        energy_intelligence = analyze_energy_breakdown(energy_breakdown)
        return dict(
            data=data,
            diagnosis=diagnosis,
            recommendations=recommendations,
            savings=savings,
            carbon=carbon,
            energy_breakdown=energy_breakdown,
            energy_intelligence=energy_intelligence,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc

@app.get('/')
def home():
    return FileResponse(ROOT/'web'/'index.html')



# ENERGIA_CONSUMPTION_SESSION_API_V8
@app.get("/api/consumption/session")
def get_energy_consumption_session(request: Request):
    """Consulter les donnees energetiques de la session."""

    from consumption_session import (
        get_authenticated_consumption_key,
        get_consumption_session,
    )

    session_key = get_authenticated_consumption_key(request)
    report = get_consumption_session(session_key)

    if report is None:
        return {
            "success": True,
            "available": False,
            "message": (
                "Aucune consommation importee "
                "pour cette session."
            ),
        }

    return {
        "success": True,
        "available": True,
        "record_count": report.get("record_count", 0),
        "analysis": report.get("analysis", {}),
        "anomalies": report.get("anomalies", {}),
        "comparison": report.get("comparison", {}),
        "insights": report.get("insights", {}),
    }



# ENERGIA_CONSUMPTION_QA_API_V8
class ConsumptionQuestionInput(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@app.post("/api/consumption/ask")
def ask_consumption_question(
    payload: ConsumptionQuestionInput,
    request: Request
):
    """Interroger les consommations de la session authentifiee."""

    from consumption_session import (
        get_authenticated_consumption_key,
        get_consumption_session,
    )
    from consumption_qa import answer_consumption_question

    session_key = get_authenticated_consumption_key(request)
    report = get_consumption_session(session_key)

    if report is None:
        return {
            "success": True,
            "answered": False,
            "answer": (
                "Aucune donnee energetique n'est disponible "
                "pour cette session. Importez d'abord "
                "un fichier CSV ou Excel."
            ),
            "source": "consumption_session",
        }

    result = answer_consumption_question(
        payload.question,
        report
    )

    return {
        "success": True,
        "answered": result.get("answered", False),
        "answer": result.get("answer", ""),
        "source": result.get("source", "consumption_qa"),
    }



# ENERGIA_COMBINED_ANALYSIS_API_V8
class CombinedAnalysisInput(BaseModel):
    building_result: dict
    question: str = Field(default="", max_length=1000)


@app.post("/api/consumption/combined")
def analyze_combined_consumption(
    payload: CombinedAnalysisInput,
    request: Request
):
    """Croiser diagnostic batiment et consommations importees."""

    from consumption_session import (
        get_authenticated_consumption_key,
        get_consumption_session,
    )
    from combined_energy_analysis import analyze_combined_energy
    from combined_energy_qa import answer_combined_question

    session_key = get_authenticated_consumption_key(request)
    report = get_consumption_session(session_key)

    if report is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Aucune consommation importee pour cette session. "
                "Importez un fichier CSV ou Excel."
            )
        )

    result = analyze_combined_energy(
        payload.building_result,
        report
    )

    # ENERGIA_COMBINED_QA_CONNECTION_V8
    answer = answer_combined_question(
        payload.question,
        result
    )

    return {
        "success": True,
        "combined": result,
        "answered": answer.get("answered", False),
        "answer": answer.get("answer", ""),
        "source": answer.get(
            "source", "combined_energy_analysis"
        ),
    }


@app.post("/api/consumption/import")
async def import_energy_consumption(request: Request):
    """Importer et analyser des consommations CSV/XLSX."""
    from consumption_import import import_consumption_file
    from consumption_analysis import analyze_monthly_consumption
    from consumption_anomalies import detect_consumption_anomalies
    from consumption_comparison import compare_annual_consumption
    from consumption_advisor import generate_consumption_insights
    from consumption_session import (
        get_authenticated_consumption_key,
        save_consumption_session,
    )

    max_bytes = 5 * 1024 * 1024

    try:
        form = await request.form()
        uploaded = form.get("file")

        if uploaded is None or not hasattr(uploaded, "read"):
            raise HTTPException(
                status_code=422,
                detail="Fichier manquant."
            )

        filename = getattr(uploaded, "filename", "") or ""

        if Path(filename).suffix.lower() not in (".csv", ".xlsx"):
            raise HTTPException(
                status_code=422,
                detail="Formats acceptes : CSV et XLSX."
            )

        content_bytes = await uploaded.read(max_bytes + 1)

        if len(content_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail="Fichier trop volumineux (5 Mo maximum)."
            )

        records = import_consumption_file(
            filename, content_bytes
        )

        analysis = analyze_monthly_consumption(records)
        anomalies = detect_consumption_anomalies(records)
        comparison = compare_annual_consumption(records)
        insights = generate_consumption_insights(
            analysis, anomalies, comparison
        )

        # Stockage temporaire lie a la session authentifiee.
        session_key = get_authenticated_consumption_key(request)

        save_consumption_session(
            session_key,
            {
                "filename": filename,
                "record_count": len(records),
                "records": records,
                "analysis": analysis,
                "anomalies": anomalies,
                "comparison": comparison,
                "insights": insights,
            }
        )


        return {
            "success": True,
            "filename": filename,
            "record_count": len(records),
            "records": records,
            "analysis": analysis,
            "anomalies": anomalies,
            "comparison": comparison,
            "insights": insights
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

@app.post('/api/analyze')
def analyze(payload: AuditInput):
    return calculate(payload)

@app.post('/api/ask')
def ask(payload: QuestionInput):
    result = calculate(payload.audit)
    answer, mode = ask_ai(
        payload.question,
        result['data'],
        result['recommendations'],
        analysis_context=result,
        allow_external_ai=payload.allow_external_ai
    )
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

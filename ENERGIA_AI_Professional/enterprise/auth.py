"""Session cookie and CSRF protection; no public registration."""
import os, secrets
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from argon2 import PasswordHasher
from sqlalchemy import select
from .store import Session, User

COOKIE='energia_session'
SESSION_SECONDS=8*3600
PH=PasswordHasher()
def signer():
    secret=os.getenv('ENERGIA_SESSION_SECRET','')
    if len(secret)<32: raise RuntimeError('Définir ENERGIA_SESSION_SECRET (au moins 32 caractères aléatoires).')
    return URLSafeTimedSerializer(secret,salt='energia-v8-session')
def get_user(request:Request):
    cookie=request.cookies.get(COOKIE)
    if not cookie: raise HTTPException(401,'Connexion requise')
    try: data=signer().loads(cookie,max_age=SESSION_SECONDS)
    except (BadSignature,SignatureExpired):raise HTTPException(401,'Session expirée')
    with Session() as db:
        user=db.get(User,data.get('uid'))
        if not user or user.organization_id!=data.get('org'):raise HTTPException(401,'Session invalide')
        return dict(id=user.id,email=user.email,role=user.role,organization_id=user.organization_id)
def csrf_token(request:Request):
    cookie=request.cookies.get(COOKIE)
    if not cookie: return None
    return signer().dumps({'session':cookie},salt='energia-csrf')
def verify_csrf(request:Request):
    token=request.headers.get('X-CSRF-Token','')
    try: value=URLSafeTimedSerializer(os.environ['ENERGIA_SESSION_SECRET'],salt='energia-csrf').loads(token,max_age=SESSION_SECONDS)
    except (BadSignature,SignatureExpired,KeyError):raise HTTPException(403,'Jeton CSRF manquant ou invalide')
    if value.get('session')!=request.cookies.get(COOKIE):raise HTTPException(403,'Jeton CSRF invalide')
def require_write(user):
    if user['role'] not in ('admin','engineer'):raise HTTPException(403,'Droits insuffisants')

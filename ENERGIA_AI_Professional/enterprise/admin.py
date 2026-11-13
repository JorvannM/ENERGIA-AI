"""Administration des collaborateurs, strictement limitée à l'organisation courante."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from .auth import get_user, PH
from .store import Session, User, new_id

router = APIRouter(prefix='/api/v8/admin', tags=['Administration'])
ROLES = {'admin', 'engineer', 'reader'}

def admin_only(user=Depends(get_user)):
    if user['role'] != 'admin':
        raise HTTPException(403, 'Accès réservé aux administrateurs')
    return user

class NewCollaborator(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=200)
    role: str = 'engineer'

class RoleUpdate(BaseModel):
    role: str

@router.get('/users')
def list_users(admin=Depends(admin_only)):
    with Session() as db:
        rows = db.scalars(select(User).where(User.organization_id == admin['organization_id']).order_by(User.email)).all()
        return {'users': [{'id': u.id, 'email': u.email, 'role': u.role} for u in rows]}

@router.post('/users', status_code=201)
def create_user(payload: NewCollaborator, admin=Depends(admin_only)):
    email = payload.email.strip().lower()
    if '@' not in email or not email.split('@')[-1].count('.'):
        raise HTTPException(422, 'Adresse email invalide')
    if payload.role not in ROLES:
        raise HTTPException(422, 'Rôle invalide')
    with Session.begin() as db:
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(409, 'Adresse email déjà utilisée')
        ident = new_id()
        db.add(User(id=ident, organization_id=admin['organization_id'], email=email,
                    password_hash=PH.hash(payload.password), role=payload.role))
        try:
            db.flush()
        except IntegrityError:
            raise HTTPException(409, 'Adresse email déjà utilisée')
    return {'id': ident, 'email': email, 'role': payload.role}

@router.patch('/users/{user_id}/role')
def change_role(user_id: str, payload: RoleUpdate, admin=Depends(admin_only)):
    if payload.role not in ROLES:
        raise HTTPException(422, 'Rôle invalide')
    with Session.begin() as db:
        target = db.scalar(select(User).where(User.id == user_id, User.organization_id == admin['organization_id']))
        if not target:
            raise HTTPException(404, 'Collaborateur introuvable')
        if target.role == 'admin' and payload.role != 'admin':
            count = db.scalar(select(func.count()).select_from(User).where(
                User.organization_id == admin['organization_id'], User.role == 'admin'))
            if count <= 1:
                raise HTTPException(409, 'Le dernier administrateur ne peut pas être rétrogradé')
        target.role = payload.role
    return {'id': user_id, 'role': payload.role}

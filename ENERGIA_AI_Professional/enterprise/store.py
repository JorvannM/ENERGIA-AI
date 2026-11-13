"""V8 Lot 2: SQLAlchemy storage; PostgreSQL in production, SQLite for local tests."""
import os, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_URL = os.getenv('DATABASE_URL') or 'sqlite:///' + str(BASE_DIR / 'local_data' / 'energia_enterprise.sqlite3')
if DB_URL.startswith('postgres://'): DB_URL = 'postgresql://' + DB_URL[len('postgres://'):]
if DB_URL.startswith('sqlite:'):
    (BASE_DIR / 'local_data').mkdir(exist_ok=True)
engine = create_engine(DB_URL, pool_pre_ping=True, connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite:') else {})
Session = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Organization(Base):
    __tablename__='organizations'
    id=Column(String(36),primary_key=True)
    name=Column(String(180),nullable=False)
class User(Base):
    __tablename__='users'
    id=Column(String(36),primary_key=True)
    organization_id=Column(String(36),ForeignKey('organizations.id'),nullable=False,index=True)
    email=Column(String(254),nullable=False,unique=True)
    password_hash=Column(Text,nullable=False)
    role=Column(String(20),nullable=False,default='engineer')
class Building(Base):
    __tablename__='buildings'
    id=Column(String(36),primary_key=True)
    organization_id=Column(String(36),ForeignKey('organizations.id'),nullable=False,index=True)
    name=Column(String(200),nullable=False)
    address=Column(String(400),nullable=False,default='')
    input_json=Column(Text,nullable=False)
    created_at=Column(String(40),nullable=False)
    updated_at=Column(String(40),nullable=False)
class Audit(Base):
    __tablename__='audits'
    id=Column(String(36),primary_key=True)
    organization_id=Column(String(36),ForeignKey('organizations.id'),nullable=False,index=True)
    building_id=Column(String(36),ForeignKey('buildings.id'),nullable=False,index=True)
    author_id=Column(String(36),ForeignKey('users.id'),nullable=False)
    input_json=Column(Text,nullable=False)
    result_json=Column(Text,nullable=False)
    created_at=Column(String(40),nullable=False)

def init_db(): Base.metadata.create_all(engine)
def new_id(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def save_building(org, data):
    ident=new_id();stamp=now()
    with Session.begin() as db:
        db.add(Building(id=ident,organization_id=org,name=data.get('name') or 'Bâtiment sans nom',address=data.get('address') or '',input_json=json.dumps(data,ensure_ascii=False),created_at=stamp,updated_at=stamp))
    return ident
def list_buildings(org):
    with Session() as db:
        rows=db.scalars(select(Building).where(Building.organization_id==org).order_by(Building.updated_at.desc())).all()
        return [dict(id=r.id,name=r.name,address=r.address,created_at=r.created_at,updated_at=r.updated_at) for r in rows]
def get_building(org,ident):
    with Session() as db:
        r=db.scalar(select(Building).where(Building.organization_id==org,Building.id==ident))
        return dict(id=r.id,name=r.name,address=r.address,created_at=r.created_at,updated_at=r.updated_at,input=json.loads(r.input_json)) if r else None
def save_audit(org,user,ident,inputs,results):
    aid=new_id();stamp=now()
    with Session.begin() as db:
        r=db.scalar(select(Building).where(Building.organization_id==org,Building.id==ident))
        if r is None:return None
        db.add(Audit(id=aid,organization_id=org,building_id=ident,author_id=user,input_json=json.dumps(inputs,ensure_ascii=False),result_json=json.dumps(results,ensure_ascii=False,default=str),created_at=stamp))
        r.input_json=json.dumps(inputs,ensure_ascii=False)
        r.name=inputs.get('name') or 'Bâtiment sans nom';r.address=inputs.get('address') or '';r.updated_at=stamp
    return aid
def list_audits(org,ident):
    with Session() as db:
        rows=db.scalars(select(Audit).where(Audit.organization_id==org,Audit.building_id==ident).order_by(Audit.created_at.desc())).all()
        return [dict(id=r.id,building_id=r.building_id,created_at=r.created_at,author_id=r.author_id) for r in rows]
def get_audit(org,ident,aid):
    with Session() as db:
        r=db.scalar(select(Audit).where(Audit.organization_id==org,Audit.building_id==ident,Audit.id==aid))
        return dict(id=r.id,building_id=r.building_id,created_at=r.created_at,author_id=r.author_id,input=json.loads(r.input_json),result=json.loads(r.result_json)) if r else None

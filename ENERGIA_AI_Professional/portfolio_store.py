"""Local V8 prototype persistence. Not multi-tenant; do not expose publicly."""
import json, os, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
DB_PATH=Path(os.getenv('ENERGIA_DB_PATH',str(Path(__file__).parent/'local_data'/'energia.sqlite3')))

def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB_PATH,timeout=10)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute("""CREATE TABLE IF NOT EXISTS buildings (id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT NOT NULL DEFAULT '', input_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS audits (id TEXT PRIMARY KEY, building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE, input_json TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL)""")
    return db

def now():return datetime.now(timezone.utc).isoformat()
def save_building(data):
    ident=str(uuid.uuid4()); timestamp=now()
    with connect() as db:db.execute('INSERT INTO buildings VALUES (?,?,?,?,?,?)',(ident,data.get('name') or 'Bâtiment sans nom',data.get('address') or '',json.dumps(data,ensure_ascii=False),timestamp,timestamp))
    return ident

def list_buildings():
    with connect() as db:
        rows=db.execute('SELECT id,name,address,created_at,updated_at FROM buildings ORDER BY updated_at DESC').fetchall()
        return [dict(r) for r in rows]

def get_building(ident):
    with connect() as db:
        row=db.execute('SELECT * FROM buildings WHERE id=?',(ident,)).fetchone()
        if not row:return None
        data=dict(row);data['input']=json.loads(data.pop('input_json'))
        return data

def save_audit(ident,inputs,results):
    audit_id=str(uuid.uuid4());timestamp=now()
    with connect() as db:
        if not db.execute('SELECT 1 FROM buildings WHERE id=?',(ident,)).fetchone():return None
        db.execute('INSERT INTO audits VALUES (?,?,?,?,?)',(audit_id,ident,json.dumps(inputs,ensure_ascii=False),json.dumps(results,ensure_ascii=False,default=str),timestamp))
        db.execute('UPDATE buildings SET input_json=?,name=?,address=?,updated_at=? WHERE id=?',(json.dumps(inputs,ensure_ascii=False),inputs.get('name') or 'Bâtiment sans nom',inputs.get('address') or '',timestamp,ident))
    return audit_id

def list_audits(ident):
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT id,building_id,created_at FROM audits WHERE building_id=? ORDER BY created_at DESC',(ident,))]

def get_audit(ident,audit_id):
    with connect() as db:
        row=db.execute('SELECT * FROM audits WHERE building_id=? AND id=?',(ident,audit_id)).fetchone()
        if not row:return None
        result=dict(row);result['input']=json.loads(result.pop('input_json'));result['result']=json.loads(result.pop('result_json'));return result

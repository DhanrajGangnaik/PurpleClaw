import os, logging, random, enum
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import create_engine, func, or_, desc
from sqlalchemy.orm import Session, sessionmaker

from models import *
from pc_auth import verify_password, get_password_hash, create_access_token, decode_token
from seed import seed_database

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/purpleclaw.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("purpleclaw")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def paginate(query, page: int, size: int):
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"items": [obj_to_dict(i) for i in items], "total": total, "page": page, "size": size, "pages": max(1, (total + size - 1) // size)}

def obj_to_dict(obj):
    if obj is None:
        return None
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, enum.Enum):
            val = val.value
        d[col.name] = val
    return d

app = FastAPI(title="PurpleClaw API", version="2.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            logger.info("Seeding database...")
            seed_database(db)
    except Exception as e:
        logger.error(f"Seed error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.utcnow().isoformat()}

# Auth
@app.post("/api/v1/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role.value, "email": user.email}}

@app.get("/api/v1/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return obj_to_dict(current_user)

@app.put("/api/v1/auth/me")
def update_me(data: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in data.items():
        if k in ("full_name","email","avatar_url") and hasattr(current_user, k):
            setattr(current_user, k, v)
    db.commit()
    return obj_to_dict(current_user)

@app.post("/api/v1/auth/change-password")
def change_password(data: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.get("current_password",""), current_user.hashed_password):
        raise HTTPException(400, "Current password incorrect")
    current_user.hashed_password = get_password_hash(data["new_password"])
    db.commit()
    return {"message": "Password changed"}

# Dashboard
@app.get("/api/v1/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    now = datetime.utcnow()
    total_assets = db.query(Asset).count()
    active_incidents = db.query(Incident).filter(Incident.status.notin_(["closed"])).count()
    open_alerts = db.query(Alert).filter(Alert.status == AlertStatus.open).count()
    open_findings = db.query(Finding).filter(Finding.status == FindingStatus.open).count()
    critical_findings = db.query(Finding).filter(Finding.severity == Severity.critical, Finding.status != FindingStatus.resolved).count()
    ioc_count = db.query(IOC).filter(IOC.expired == False).count()
    threat_actors = db.query(ThreatActor).filter(ThreatActor.active == True).count()
    exercises_active = db.query(Exercise).filter(Exercise.status.in_(["active","planned"])).count()
    total_ass = db.query(ComplianceAssessment).count()
    compliant_ass = db.query(ComplianceAssessment).filter(ComplianceAssessment.status == "compliant").count()
    compliance_score = round((compliant_ass/total_ass)*100,1) if total_ass > 0 else 0
    risky = db.query(Asset.risk_score).order_by(Asset.risk_score.desc()).limit(20).all()
    risk_score = round(sum(r[0] for r in risky)/len(risky),1) if risky else 0
    alerts_by_sev = {s.value: db.query(Alert).filter(Alert.severity==s).count() for s in AlertSeverity}
    findings_by_sev = {s.value: db.query(Finding).filter(Finding.severity==s).count() for s in Severity}
    incidents_by_status = {s.value: db.query(Incident).filter(Incident.status==s).count() for s in IncidentStatus}
    assets_by_type = {t.value: db.query(Asset).filter(Asset.type==t).count() for t in AssetType}
    timeline = []
    for i in range(30):
        d = now - timedelta(days=29-i)
        start = d.replace(hour=0,minute=0,second=0); end = d.replace(hour=23,minute=59,second=59)
        timeline.append({"date": d.strftime("%Y-%m-%d"), "alerts": db.query(Alert).filter(Alert.created_at.between(start,end)).count(), "findings": db.query(Finding).filter(Finding.detected_at.between(start,end)).count(), "incidents": db.query(Incident).filter(Incident.created_at.between(start,end)).count()})
    recent_alerts = db.query(Alert).order_by(desc(Alert.created_at)).limit(10).all()
    recent_incidents = db.query(Incident).order_by(desc(Incident.created_at)).limit(5).all()
    return {"total_assets": total_assets, "active_incidents": active_incidents, "open_alerts": open_alerts, "open_findings": open_findings, "critical_findings": critical_findings, "ioc_count": ioc_count, "threat_actors": threat_actors, "exercises_active": exercises_active, "compliance_score": compliance_score, "risk_score": risk_score, "alerts_by_severity": alerts_by_sev, "findings_by_severity": findings_by_sev, "incidents_by_status": incidents_by_status, "assets_by_type": assets_by_type, "timeline": timeline, "recent_alerts": [obj_to_dict(a) for a in recent_alerts], "recent_incidents": [obj_to_dict(i) for i in recent_incidents]}

@app.get("/api/v1/dashboard/posture")
def posture(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    critical = db.query(Finding).filter(Finding.severity==Severity.critical, Finding.status!=FindingStatus.resolved).count()
    high = db.query(Finding).filter(Finding.severity==Severity.high, Finding.status!=FindingStatus.resolved).count()
    covered = db.query(ATTACKCoverage).filter(ATTACKCoverage.covered==True).count()
    total_cov = db.query(ATTACKCoverage).count()
    total_ass = db.query(ComplianceAssessment).count()
    compliant_ass = db.query(ComplianceAssessment).filter(ComplianceAssessment.status=="compliant").count()
    score = min(100, max(0, 100-(critical*8)-(high*3)))
    return {"overall_score": round(score,1), "vulnerability_score": round(max(0,100-critical*10-high*5),1), "detection_score": round((covered/total_cov*100) if total_cov else 0,1), "compliance_score": round((compliant_ass/total_ass*100) if total_ass else 0,1), "incident_score": 72.0, "components": {"vulnerability_mgmt": round(max(0,100-critical*8),1), "detection_coverage": round((covered/total_cov*100) if total_cov else 0,1), "incident_response": 72.0, "compliance": round((compliant_ass/total_ass*100) if total_ass else 0,1), "threat_intel": 68.0, "asset_mgmt": 85.0}}

# Users
@app.get("/api/v1/users")
def list_users(page:int=1,size:int=20,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(User)
    if search: q=q.filter(or_(User.username.ilike(f"%{search}%"),User.full_name.ilike(f"%{search}%"),User.email.ilike(f"%{search}%")))
    return paginate(q.order_by(User.id),page,size)

@app.post("/api/v1/users")
def create_user(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.admin: raise HTTPException(403,"Admin required")
    if db.query(User).filter(User.username==data["username"]).first(): raise HTTPException(400,"Username exists")
    u=User(username=data["username"],email=data["email"],hashed_password=get_password_hash(data["password"]),full_name=data.get("full_name"),role=UserRole(data.get("role","viewer")))
    db.add(u); db.commit(); db.refresh(u); return obj_to_dict(u)

@app.get("/api/v1/users/{user_id}")
def get_user(user_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(404,"User not found")
    return obj_to_dict(u)

@app.put("/api/v1/users/{user_id}")
def update_user(user_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.admin and current_user.id!=user_id: raise HTTPException(403,"Forbidden")
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if k=="role" and current_user.role==UserRole.admin: u.role=UserRole(v)
        elif k in ("full_name","email","is_active") and hasattr(u,k): setattr(u,k,v)
    db.commit(); return obj_to_dict(u)

@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.admin: raise HTTPException(403,"Admin required")
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(404,"Not found")
    db.delete(u); db.commit(); return {"message":"User deleted"}

@app.post("/api/v1/users/{user_id}/reset-password")
def reset_password(user_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.admin: raise HTTPException(403,"Admin required")
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(404,"Not found")
    u.hashed_password=get_password_hash(data["new_password"]); db.commit(); return {"message":"Password reset"}

# Assets
@app.get("/api/v1/assets")
def list_assets(page:int=1,size:int=20,search:Optional[str]=None,type:Optional[str]=None,status:Optional[str]=None,criticality:Optional[str]=None,group:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Asset)
    if search: q=q.filter(or_(Asset.name.ilike(f"%{search}%"),Asset.hostname.ilike(f"%{search}%"),Asset.ip_address.ilike(f"%{search}%")))
    if type: q=q.filter(Asset.type==AssetType(type))
    if status: q=q.filter(Asset.status==AssetStatus(status))
    if criticality: q=q.filter(Asset.criticality==Criticality(criticality))
    if group: q=q.filter(Asset.group_name.ilike(f"%{group}%"))
    return paginate(q.order_by(desc(Asset.risk_score)),page,size)

@app.get("/api/v1/assets/stats")
def asset_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_type":{t.value:db.query(Asset).filter(Asset.type==t).count() for t in AssetType},"by_status":{s.value:db.query(Asset).filter(Asset.status==s).count() for s in AssetStatus},"by_criticality":{c.value:db.query(Asset).filter(Asset.criticality==c).count() for c in Criticality},"total":db.query(Asset).count()}

@app.get("/api/v1/assets/risky")
def risky_assets(limit:int=10,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(a) for a in db.query(Asset).order_by(desc(Asset.risk_score)).limit(limit).all()]

@app.post("/api/v1/assets")
def create_asset(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=Asset(name=data["name"],type=AssetType(data["type"]),ip_address=data.get("ip_address"),hostname=data.get("hostname"),os=data.get("os"),os_version=data.get("os_version"),criticality=Criticality(data.get("criticality","medium")),status=AssetStatus(data.get("status","active")),owner=data.get("owner"),location=data.get("location"),department=data.get("department"),group_name=data.get("group_name"),tags=data.get("tags",[]),risk_score=data.get("risk_score",0.0))
    db.add(a); db.commit(); db.refresh(a); return obj_to_dict(a)

@app.get("/api/v1/assets/{asset_id}")
def get_asset(asset_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Asset).filter(Asset.id==asset_id).first()
    if not a: raise HTTPException(404,"Asset not found")
    d=obj_to_dict(a)
    d["findings_count"]=db.query(Finding).filter(Finding.asset_id==asset_id,Finding.status!=FindingStatus.resolved).count()
    return d

@app.put("/api/v1/assets/{asset_id}")
def update_asset(asset_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Asset).filter(Asset.id==asset_id).first()
    if not a: raise HTTPException(404,"Not found")
    allowed=("name","ip_address","hostname","os","os_version","owner","location","department","group_name","tags","open_ports","services","risk_score","notes")
    for k,v in data.items():
        if k=="status": a.status=AssetStatus(v)
        elif k=="criticality": a.criticality=Criticality(v)
        elif k in allowed: setattr(a,k,v)
    db.commit(); return obj_to_dict(a)

@app.delete("/api/v1/assets/{asset_id}")
def delete_asset(asset_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Asset).filter(Asset.id==asset_id).first()
    if not a: raise HTTPException(404,"Not found")
    db.delete(a); db.commit(); return {"message":"Asset deleted"}

@app.get("/api/v1/assets/{asset_id}/findings")
def asset_findings(asset_id:int,page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(Finding).filter(Finding.asset_id==asset_id).order_by(desc(Finding.risk_score)),page,size)

# Alerts
@app.get("/api/v1/alerts")
def list_alerts(page:int=1,size:int=20,severity:Optional[str]=None,status:Optional[str]=None,source:Optional[str]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Alert)
    if severity: q=q.filter(Alert.severity==AlertSeverity(severity))
    if status: q=q.filter(Alert.status==AlertStatus(status))
    if source: q=q.filter(Alert.source.ilike(f"%{source}%"))
    if search: q=q.filter(or_(Alert.title.ilike(f"%{search}%"),Alert.description.ilike(f"%{search}%")))
    return paginate(q.order_by(desc(Alert.created_at)),page,size)

@app.get("/api/v1/alerts/stats")
def alert_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_severity":{s.value:db.query(Alert).filter(Alert.severity==s).count() for s in AlertSeverity},"by_status":{s.value:db.query(Alert).filter(Alert.status==s).count() for s in AlertStatus},"total":db.query(Alert).count(),"open":db.query(Alert).filter(Alert.status==AlertStatus.open).count()}

@app.post("/api/v1/alerts")
def create_alert(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=Alert(title=data["title"],description=data.get("description",""),severity=AlertSeverity(data.get("severity","medium")),source=data.get("source","manual"),mitre_techniques=data.get("mitre_techniques",[]),tags=data.get("tags",[]))
    db.add(a); db.commit(); db.refresh(a); return obj_to_dict(a)

@app.get("/api/v1/alerts/{alert_id}")
def get_alert(alert_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Alert not found")
    return obj_to_dict(a)

@app.put("/api/v1/alerts/{alert_id}")
def update_alert(alert_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if k=="status": a.status=AlertStatus(v)
        elif k=="severity": a.severity=AlertSeverity(v)
        elif hasattr(a,k): setattr(a,k,v)
    db.commit(); return obj_to_dict(a)

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
def ack_alert(alert_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Not found")
    a.status=AlertStatus.investigating; a.acknowledged_at=datetime.utcnow(); a.assignee_id=current_user.id
    db.commit(); return obj_to_dict(a)

@app.post("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(alert_id:int,data:dict=Body(default={}),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Not found")
    a.status=AlertStatus.resolved; a.resolved_at=datetime.utcnow()
    db.commit(); return obj_to_dict(a)

@app.post("/api/v1/alerts/{alert_id}/escalate")
def escalate_alert(alert_id:int,data:dict=Body(default={}),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Not found")
    inc=Incident(title=data.get("title",f"Incident: {a.title}"),description=a.description or "",severity=IncidentSeverity.high,status=IncidentStatus.new,assignee_id=current_user.id,alert_ids=[a.id])
    db.add(inc); db.flush(); a.incident_id=inc.id; db.commit()
    return {"incident":obj_to_dict(inc),"alert":obj_to_dict(a)}

# Alert Rules
@app.get("/api/v1/alert-rules")
def list_alert_rules(page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(AlertRule).order_by(AlertRule.id),page,size)

@app.post("/api/v1/alert-rules")
def create_alert_rule(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    r=AlertRule(name=data["name"],description=data.get("description",""),query=data.get("query",""),severity=AlertSeverity(data.get("severity","medium")),rule_type=data.get("rule_type","threshold"),tags=data.get("tags",[]),mitre_techniques=data.get("mitre_techniques",[]),threshold=data.get("threshold",1),window_minutes=data.get("window_minutes",60),created_by_id=current_user.id)
    db.add(r); db.commit(); db.refresh(r); return obj_to_dict(r)

@app.put("/api/v1/alert-rules/{rule_id}")
def update_alert_rule(rule_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(AlertRule).filter(AlertRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(r,k): setattr(r,k,AlertSeverity(v) if k=="severity" else v)
    db.commit(); return obj_to_dict(r)

@app.delete("/api/v1/alert-rules/{rule_id}")
def delete_alert_rule(rule_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(AlertRule).filter(AlertRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    db.delete(r); db.commit(); return {"message":"Rule deleted"}

@app.post("/api/v1/alert-rules/{rule_id}/toggle")
def toggle_rule(rule_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(AlertRule).filter(AlertRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    r.enabled=not r.enabled; db.commit(); return obj_to_dict(r)

# Incidents
@app.get("/api/v1/incidents")
def list_incidents(page:int=1,size:int=20,severity:Optional[str]=None,status:Optional[str]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Incident)
    if severity: q=q.filter(Incident.severity==IncidentSeverity(severity))
    if status: q=q.filter(Incident.status==IncidentStatus(status))
    if search: q=q.filter(Incident.title.ilike(f"%{search}%"))
    return paginate(q.order_by(desc(Incident.created_at)),page,size)

@app.get("/api/v1/incidents/stats")
def incident_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_status":{s.value:db.query(Incident).filter(Incident.status==s).count() for s in IncidentStatus},"by_severity":{s.value:db.query(Incident).filter(Incident.severity==s).count() for s in IncidentSeverity},"total":db.query(Incident).count()}

@app.post("/api/v1/incidents")
def create_incident(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    inc=Incident(title=data["title"],description=data.get("description",""),severity=IncidentSeverity(data.get("severity","medium")),status=IncidentStatus.new,assignee_id=current_user.id,tlp=data.get("tlp","TLP:AMBER"),impact=data.get("impact",""),attack_vector=data.get("attack_vector"))
    db.add(inc); db.commit(); db.refresh(inc); return obj_to_dict(inc)

@app.get("/api/v1/incidents/{inc_id}")
def get_incident(inc_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    inc=db.query(Incident).filter(Incident.id==inc_id).first()
    if not inc: raise HTTPException(404,"Not found")
    d=obj_to_dict(inc)
    d["events"]=[obj_to_dict(e) for e in db.query(IncidentEvent).filter(IncidentEvent.incident_id==inc_id).order_by(IncidentEvent.timestamp).all()]
    d["tasks"]=[obj_to_dict(t) for t in db.query(IncidentTask).filter(IncidentTask.incident_id==inc_id).all()]
    return d

@app.put("/api/v1/incidents/{inc_id}")
def update_incident(inc_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    inc=db.query(Incident).filter(Incident.id==inc_id).first()
    if not inc: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if k=="status": inc.status=IncidentStatus(v); (setattr(inc,"resolved_at",datetime.utcnow()) if v=="closed" else None)
        elif k=="severity": inc.severity=IncidentSeverity(v)
        elif hasattr(inc,k): setattr(inc,k,v)
    db.commit(); return obj_to_dict(inc)

@app.post("/api/v1/incidents/{inc_id}/events")
def add_incident_event(inc_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    ev=IncidentEvent(incident_id=inc_id,user_id=current_user.id,action=data.get("action","note"),details=data.get("details",""),event_type=data.get("event_type","note"))
    db.add(ev); db.commit(); db.refresh(ev); return obj_to_dict(ev)

@app.get("/api/v1/incidents/{inc_id}/events")
def list_incident_events(inc_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(e) for e in db.query(IncidentEvent).filter(IncidentEvent.incident_id==inc_id).order_by(IncidentEvent.timestamp).all()]

@app.post("/api/v1/incidents/{inc_id}/tasks")
def add_incident_task(inc_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    t=IncidentTask(incident_id=inc_id,title=data["title"],description=data.get("description",""),status="open",priority=data.get("priority","medium"),assignee_id=data.get("assignee_id"))
    db.add(t); db.commit(); db.refresh(t); return obj_to_dict(t)

@app.put("/api/v1/incidents/{inc_id}/tasks/{task_id}")
def update_incident_task(inc_id:int,task_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    t=db.query(IncidentTask).filter(IncidentTask.id==task_id,IncidentTask.incident_id==inc_id).first()
    if not t: raise HTTPException(404,"Task not found")
    for k,v in data.items():
        if hasattr(t,k): setattr(t,k,v)
    if data.get("status")=="completed": t.completed_at=datetime.utcnow()
    db.commit(); return obj_to_dict(t)

# Cases
@app.get("/api/v1/cases")
def list_cases(page:int=1,size:int=20,status:Optional[str]=None,priority:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Case)
    if status: q=q.filter(Case.status==status)
    if priority: q=q.filter(Case.priority==priority)
    return paginate(q.order_by(desc(Case.created_at)),page,size)

@app.post("/api/v1/cases")
def create_case(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    c=Case(title=data["title"],description=data.get("description",""),incident_id=data.get("incident_id"),status="open",priority=data.get("priority","medium"),assignee_id=current_user.id,tlp=data.get("tlp","TLP:GREEN"))
    db.add(c); db.commit(); db.refresh(c); return obj_to_dict(c)

@app.get("/api/v1/cases/{case_id}")
def get_case(case_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=db.query(Case).filter(Case.id==case_id).first()
    if not c: raise HTTPException(404,"Not found")
    d=obj_to_dict(c)
    d["notes"]=[obj_to_dict(n) for n in db.query(CaseNote).filter(CaseNote.case_id==case_id).order_by(CaseNote.created_at).all()]
    d["evidence"]=[obj_to_dict(e) for e in db.query(CaseEvidence).filter(CaseEvidence.case_id==case_id).all()]
    return d

@app.post("/api/v1/cases/{case_id}/notes")
def add_case_note(case_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    n=CaseNote(case_id=case_id,user_id=current_user.id,content=data["content"])
    db.add(n); db.commit(); db.refresh(n); return obj_to_dict(n)

@app.post("/api/v1/cases/{case_id}/evidence")
def add_case_evidence(case_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    ev=CaseEvidence(case_id=case_id,user_id=current_user.id,type=data.get("type","file"),name=data["name"],description=data.get("description",""),file_hash=data.get("file_hash"),file_path=data.get("file_path"))
    db.add(ev); db.commit(); db.refresh(ev); return obj_to_dict(ev)

# SIEM
@app.get("/api/v1/siem/events")
def list_log_events(page:int=1,size:int=50,level:Optional[str]=None,category:Optional[str]=None,source_ip:Optional[str]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(LogEvent)
    if level: q=q.filter(LogEvent.level==level)
    if category: q=q.filter(LogEvent.category==category)
    if source_ip: q=q.filter(LogEvent.source_ip.ilike(f"%{source_ip}%"))
    if search: q=q.filter(LogEvent.message.ilike(f"%{search}%"))
    return paginate(q.order_by(desc(LogEvent.timestamp)),page,size)

@app.get("/api/v1/siem/events/stats")
def siem_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    levels=["info","warning","error","critical"]
    cats=["authentication","network","process","file","dns","registry","other"]
    return {"by_level":{l:db.query(LogEvent).filter(LogEvent.level==l).count() for l in levels},"by_category":{c:db.query(LogEvent).filter(LogEvent.category==c).count() for c in cats},"total":db.query(LogEvent).count(),"sources":db.query(LogSource).count()}

@app.post("/api/v1/siem/events")
def ingest_event(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ev=LogEvent(level=data.get("level","info"),category=data.get("category","other"),message=data.get("message",""),raw=data.get("raw",""),source_ip=data.get("source_ip"),username=data.get("username"),parsed_fields=data.get("parsed_fields",{}))
    db.add(ev); db.commit(); db.refresh(ev); return obj_to_dict(ev)

@app.get("/api/v1/siem/sources")
def list_log_sources(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(s) for s in db.query(LogSource).all()]

@app.post("/api/v1/siem/sources")
def create_log_source(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    s=LogSource(name=data["name"],type=data.get("type","api"),config=data.get("config",{}))
    db.add(s); db.commit(); db.refresh(s); return obj_to_dict(s)

@app.get("/api/v1/siem/rules")
def list_detection_rules(page:int=1,size:int=20,enabled:Optional[bool]=None,severity:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(DetectionRule)
    if enabled is not None: q=q.filter(DetectionRule.enabled==enabled)
    if severity: q=q.filter(DetectionRule.severity==AlertSeverity(severity))
    return paginate(q.order_by(DetectionRule.id),page,size)

@app.post("/api/v1/siem/rules")
def create_detection_rule(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    r=DetectionRule(name=data["name"],description=data.get("description",""),logic=data.get("logic",""),severity=AlertSeverity(data.get("severity","medium")),rule_type=data.get("rule_type","sigma"),tags=data.get("tags",[]),mitre_techniques=data.get("mitre_techniques",[]),created_by_id=current_user.id)
    db.add(r); db.commit(); db.refresh(r); return obj_to_dict(r)

@app.put("/api/v1/siem/rules/{rule_id}")
def update_detection_rule(rule_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(DetectionRule).filter(DetectionRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(r,k): setattr(r,k,AlertSeverity(v) if k=="severity" else v)
    db.commit(); return obj_to_dict(r)

@app.delete("/api/v1/siem/rules/{rule_id}")
def delete_detection_rule(rule_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(DetectionRule).filter(DetectionRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    db.delete(r); db.commit(); return {"message":"Rule deleted"}

@app.post("/api/v1/siem/rules/{rule_id}/toggle")
def toggle_detection_rule(rule_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(DetectionRule).filter(DetectionRule.id==rule_id).first()
    if not r: raise HTTPException(404,"Not found")
    r.enabled=not r.enabled; db.commit(); return obj_to_dict(r)

# Threat Intel
@app.get("/api/v1/intel/iocs")
def list_iocs(page:int=1,size:int=20,type:Optional[str]=None,severity:Optional[str]=None,expired:Optional[bool]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(IOC)
    if type: q=q.filter(IOC.type==IOCType(type))
    if severity: q=q.filter(IOC.severity==Severity(severity))
    if expired is not None: q=q.filter(IOC.expired==expired)
    if search: q=q.filter(IOC.value.ilike(f"%{search}%"))
    return paginate(q.order_by(desc(IOC.created_at)),page,size)

@app.post("/api/v1/intel/iocs")
def create_ioc(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ioc=IOC(type=IOCType(data["type"]),value=data["value"],severity=Severity(data.get("severity","medium")),confidence=data.get("confidence",50),source=data.get("source","manual"),description=data.get("description",""),tags=data.get("tags",[]),first_seen=datetime.utcnow(),last_seen=datetime.utcnow())
    db.add(ioc); db.commit(); db.refresh(ioc); return obj_to_dict(ioc)

@app.get("/api/v1/intel/iocs/{ioc_id}")
def get_ioc(ioc_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ioc=db.query(IOC).filter(IOC.id==ioc_id).first()
    if not ioc: raise HTTPException(404,"Not found")
    return obj_to_dict(ioc)

@app.put("/api/v1/intel/iocs/{ioc_id}")
def update_ioc(ioc_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ioc=db.query(IOC).filter(IOC.id==ioc_id).first()
    if not ioc: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(ioc,k): setattr(ioc,k,v)
    db.commit(); return obj_to_dict(ioc)

@app.post("/api/v1/intel/iocs/lookup")
def lookup_ioc(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    value=data.get("value","")
    matches=db.query(IOC).filter(IOC.value.ilike(f"%{value}%")).limit(10).all()
    return {"matches":[obj_to_dict(m) for m in matches],"count":len(matches)}

@app.get("/api/v1/intel/stats")
def intel_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"total_iocs":db.query(IOC).count(),"active_iocs":db.query(IOC).filter(IOC.expired==False).count(),"actors_tracked":db.query(ThreatActor).count(),"active_campaigns":db.query(Campaign).filter(Campaign.status=="active").count(),"feeds_active":db.query(ThreatFeed).filter(ThreatFeed.enabled==True).count(),"by_type":{t.value:db.query(IOC).filter(IOC.type==t).count() for t in IOCType},"by_severity":{s.value:db.query(IOC).filter(IOC.severity==s).count() for s in Severity}}

@app.get("/api/v1/intel/actors")
def list_actors(page:int=1,size:int=20,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(ThreatActor)
    if search: q=q.filter(ThreatActor.name.ilike(f"%{search}%"))
    return paginate(q.order_by(ThreatActor.name),page,size)

@app.post("/api/v1/intel/actors")
def create_actor(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=ThreatActor(name=data["name"],aliases=data.get("aliases",[]),description=data.get("description",""),motivation=data.get("motivation",[]),sophistication=data.get("sophistication","organized"),country=data.get("country"),active=data.get("active",True),ttps=data.get("ttps",[]),target_sectors=data.get("target_sectors",[]),tools=data.get("tools",[]),first_seen=datetime.utcnow(),last_seen=datetime.utcnow())
    db.add(a); db.commit(); db.refresh(a); return obj_to_dict(a)

@app.get("/api/v1/intel/actors/{actor_id}")
def get_actor(actor_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    a=db.query(ThreatActor).filter(ThreatActor.id==actor_id).first()
    if not a: raise HTTPException(404,"Not found")
    d=obj_to_dict(a)
    d["campaigns"]=[obj_to_dict(c) for c in db.query(Campaign).filter(Campaign.actor_id==actor_id).all()]
    return d

@app.get("/api/v1/intel/campaigns")
def list_campaigns(page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(Campaign).order_by(desc(Campaign.created_at)),page,size)

@app.post("/api/v1/intel/campaigns")
def create_campaign(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=Campaign(name=data["name"],description=data.get("description",""),actor_id=data.get("actor_id"),status=data.get("status","active"),targets=data.get("targets",[]),ttps=data.get("ttps",[]))
    db.add(c); db.commit(); db.refresh(c); return obj_to_dict(c)

@app.get("/api/v1/intel/campaigns/{camp_id}")
def get_campaign(camp_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=db.query(Campaign).filter(Campaign.id==camp_id).first()
    if not c: raise HTTPException(404,"Not found")
    d=obj_to_dict(c)
    if c.actor_id:
        actor=db.query(ThreatActor).filter(ThreatActor.id==c.actor_id).first()
        d["actor"]=obj_to_dict(actor)
    return d

@app.get("/api/v1/intel/feeds")
def list_feeds(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(f) for f in db.query(ThreatFeed).all()]

@app.post("/api/v1/intel/feeds")
def create_feed(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=ThreatFeed(name=data["name"],type=data.get("type","JSON"),url=data.get("url",""),format=data.get("format","JSON"),enabled=data.get("enabled",True))
    db.add(f); db.commit(); db.refresh(f); return obj_to_dict(f)

@app.put("/api/v1/intel/feeds/{feed_id}")
def update_feed(feed_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=db.query(ThreatFeed).filter(ThreatFeed.id==feed_id).first()
    if not f: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(f,k): setattr(f,k,v)
    db.commit(); return obj_to_dict(f)

@app.post("/api/v1/intel/feeds/{feed_id}/sync")
def sync_feed(feed_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=db.query(ThreatFeed).filter(ThreatFeed.id==feed_id).first()
    if not f: raise HTTPException(404,"Not found")
    f.last_fetched=datetime.utcnow(); f.ioc_count+=random.randint(10,100)
    db.commit(); return {"message":"Feed synced","feed":obj_to_dict(f)}

# Vulns
@app.get("/api/v1/vulns")
def list_vulns(page:int=1,size:int=20,severity:Optional[str]=None,exploit_available:Optional[bool]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Vulnerability)
    if severity: q=q.filter(Vulnerability.severity==Severity(severity))
    if exploit_available is not None: q=q.filter(Vulnerability.exploit_available==exploit_available)
    if search: q=q.filter(or_(Vulnerability.cve_id.ilike(f"%{search}%"),Vulnerability.title.ilike(f"%{search}%")))
    return paginate(q.order_by(desc(Vulnerability.cvss_score)),page,size)

@app.get("/api/v1/vulns/stats")
def vuln_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_severity":{s.value:db.query(Vulnerability).filter(Vulnerability.severity==s).count() for s in Severity},"total":db.query(Vulnerability).count(),"with_exploit":db.query(Vulnerability).filter(Vulnerability.exploit_available==True).count(),"in_wild":db.query(Vulnerability).filter(Vulnerability.exploit_in_wild==True).count()}

@app.get("/api/v1/vulns/{vuln_id}")
def get_vuln(vuln_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    v=db.query(Vulnerability).filter(Vulnerability.id==vuln_id).first()
    if not v: raise HTTPException(404,"Not found")
    d=obj_to_dict(v); d["findings_count"]=db.query(Finding).filter(Finding.vulnerability_id==vuln_id).count(); return d

@app.post("/api/v1/vulns")
def create_vuln(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    v=Vulnerability(cve_id=data.get("cve_id"),title=data["title"],description=data.get("description",""),cvss_score=data.get("cvss_score",0.0),severity=Severity(data.get("severity","medium")),exploit_available=data.get("exploit_available",False))
    db.add(v); db.commit(); db.refresh(v); return obj_to_dict(v)

# Findings
@app.get("/api/v1/findings")
def list_findings(page:int=1,size:int=20,severity:Optional[str]=None,status:Optional[str]=None,asset_id:Optional[int]=None,source:Optional[str]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Finding)
    if severity: q=q.filter(Finding.severity==Severity(severity))
    if status: q=q.filter(Finding.status==FindingStatus(status))
    if asset_id: q=q.filter(Finding.asset_id==asset_id)
    if source: q=q.filter(Finding.source==source)
    if search: q=q.filter(Finding.title.ilike(f"%{search}%"))
    return paginate(q.order_by(desc(Finding.risk_score)),page,size)

@app.get("/api/v1/findings/stats")
def finding_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_severity":{s.value:db.query(Finding).filter(Finding.severity==s).count() for s in Severity},"by_status":{s.value:db.query(Finding).filter(Finding.status==s).count() for s in FindingStatus},"by_source":{src:db.query(Finding).filter(Finding.source==src).count() for src in ["scan","manual","intelligence","siem"]},"total":db.query(Finding).count(),"open":db.query(Finding).filter(Finding.status==FindingStatus.open).count()}

@app.post("/api/v1/findings")
def create_finding(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=Finding(asset_id=data.get("asset_id"),title=data["title"],description=data.get("description",""),severity=Severity(data.get("severity","medium")),source=data.get("source","manual"),risk_score=data.get("risk_score",0.0),remediation=data.get("remediation",""))
    db.add(f); db.commit(); db.refresh(f); return obj_to_dict(f)

@app.get("/api/v1/findings/{finding_id}")
def get_finding(finding_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=db.query(Finding).filter(Finding.id==finding_id).first()
    if not f: raise HTTPException(404,"Not found")
    d=obj_to_dict(f)
    if f.asset_id: d["asset"]=obj_to_dict(db.query(Asset).filter(Asset.id==f.asset_id).first())
    if f.vulnerability_id: d["vulnerability"]=obj_to_dict(db.query(Vulnerability).filter(Vulnerability.id==f.vulnerability_id).first())
    return d

@app.put("/api/v1/findings/{finding_id}")
def update_finding(finding_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    f=db.query(Finding).filter(Finding.id==finding_id).first()
    if not f: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if k=="status": f.status=FindingStatus(v); (setattr(f,"resolved_at",datetime.utcnow()) if v=="resolved" else None)
        elif k=="severity": f.severity=Severity(v)
        elif hasattr(f,k): setattr(f,k,v)
    db.commit(); return obj_to_dict(f)

@app.post("/api/v1/findings/{finding_id}/remediate")
def create_remediation(finding_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=RemediationTask(finding_id=finding_id,title=data.get("title","Remediate finding"),description=data.get("description",""),status="open",priority=data.get("priority","medium"),assignee_id=data.get("assignee_id",current_user.id),notes=data.get("notes",""))
    db.add(t); db.commit(); db.refresh(t); return obj_to_dict(t)

@app.get("/api/v1/findings/{finding_id}/remediation-tasks")
def list_finding_remediations(finding_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(t) for t in db.query(RemediationTask).filter(RemediationTask.finding_id==finding_id).all()]

@app.get("/api/v1/remediation")
def list_all_remediation(page:int=1,size:int=20,status:Optional[str]=None,priority:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(RemediationTask)
    if status: q=q.filter(RemediationTask.status==status)
    if priority: q=q.filter(RemediationTask.priority==priority)
    return paginate(q.order_by(desc(RemediationTask.created_at)),page,size)

@app.put("/api/v1/remediation/{task_id}")
def update_remediation(task_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    t=db.query(RemediationTask).filter(RemediationTask.id==task_id).first()
    if not t: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(t,k): setattr(t,k,v)
    db.commit(); return obj_to_dict(t)

# Scans
@app.get("/api/v1/scans")
def list_scans(page:int=1,size:int=20,status:Optional[str]=None,type:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(ScanJob)
    if status: q=q.filter(ScanJob.status==ScanStatus(status))
    if type: q=q.filter(ScanJob.type==type)
    return paginate(q.order_by(desc(ScanJob.created_at)),page,size)

@app.post("/api/v1/scans")
def create_scan(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    sj=ScanJob(name=data.get("name",f"Scan {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"),target=data["target"],type=data.get("type","vulnerability"),policy=data.get("policy","quick"),scanner=data.get("scanner","internal"),status=ScanStatus.pending,created_by_id=current_user.id)
    db.add(sj); db.commit(); db.refresh(sj); return obj_to_dict(sj)

@app.get("/api/v1/scans/stats")
def scan_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return {"by_status":{s.value:db.query(ScanJob).filter(ScanJob.status==s).count() for s in ScanStatus},"by_type":{t:db.query(ScanJob).filter(ScanJob.type==t).count() for t in ["vulnerability","web","port","compliance"]},"total":db.query(ScanJob).count(),"total_findings":db.query(ScanResult).count()}

@app.get("/api/v1/scans/{scan_id}")
def get_scan(scan_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    sj=db.query(ScanJob).filter(ScanJob.id==scan_id).first()
    if not sj: raise HTTPException(404,"Not found")
    d=obj_to_dict(sj); d["results_summary"]={"critical":sj.critical_count,"high":sj.high_count,"total":sj.findings_count}; return d

@app.get("/api/v1/scans/{scan_id}/results")
def scan_results(scan_id:int,page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(ScanResult).filter(ScanResult.job_id==scan_id).order_by(desc(ScanResult.created_at)),page,size)

# Red Team
@app.get("/api/v1/redteam/plans")
def list_plans(page:int=1,size:int=20,status:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(AttackPlan)
    if status: q=q.filter(AttackPlan.status==status)
    return paginate(q.order_by(desc(AttackPlan.created_at)),page,size)

@app.post("/api/v1/redteam/plans")
def create_plan(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    p=AttackPlan(name=data["name"],description=data.get("description",""),objective=data.get("objective",""),target_scope=data.get("target_scope",[]),mitre_tactics=data.get("mitre_tactics",[]),mitre_techniques=data.get("mitre_techniques",[]),team=data.get("team",""),status="draft",authorization_level=data.get("authorization_level","assumed_breach"),rules_of_engagement=data.get("rules_of_engagement",""),created_by_id=current_user.id)
    db.add(p); db.commit(); db.refresh(p); return obj_to_dict(p)

@app.get("/api/v1/redteam/plans/{plan_id}")
def get_plan(plan_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    p=db.query(AttackPlan).filter(AttackPlan.id==plan_id).first()
    if not p: raise HTTPException(404,"Not found")
    d=obj_to_dict(p); d["executions"]=[obj_to_dict(e) for e in db.query(AttackExecution).filter(AttackExecution.plan_id==plan_id).all()]; return d

@app.put("/api/v1/redteam/plans/{plan_id}")
def update_plan(plan_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    p=db.query(AttackPlan).filter(AttackPlan.id==plan_id).first()
    if not p: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(p,k): setattr(p,k,v)
    db.commit(); return obj_to_dict(p)

@app.post("/api/v1/redteam/plans/{plan_id}/approve")
def approve_plan(plan_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    p=db.query(AttackPlan).filter(AttackPlan.id==plan_id).first()
    if not p: raise HTTPException(404,"Not found")
    p.status="approved"; p.approved_by_id=current_user.id; db.commit(); return obj_to_dict(p)

@app.get("/api/v1/redteam/executions")
def list_executions(page:int=1,size:int=20,status:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(AttackExecution)
    if status: q=q.filter(AttackExecution.status==status)
    return paginate(q.order_by(desc(AttackExecution.created_at)),page,size)

@app.post("/api/v1/redteam/executions")
def create_execution(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    ex=AttackExecution(plan_id=data["plan_id"],name=data.get("name","Execution"),operator=data.get("operator",current_user.full_name),status="pending",notes=data.get("notes",""))
    db.add(ex); db.commit(); db.refresh(ex); return obj_to_dict(ex)

@app.get("/api/v1/redteam/executions/{exec_id}")
def get_execution(exec_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ex=db.query(AttackExecution).filter(AttackExecution.id==exec_id).first()
    if not ex: raise HTTPException(404,"Not found")
    d=obj_to_dict(ex); d["steps"]=[obj_to_dict(s) for s in db.query(AttackStep).filter(AttackStep.execution_id==exec_id).order_by(AttackStep.step_order).all()]; return d

@app.post("/api/v1/redteam/executions/{exec_id}/steps")
def add_step(exec_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    s=AttackStep(execution_id=exec_id,technique_id=data.get("technique_id","T1000"),step_order=data.get("step_order",1),name=data["name"],description=data.get("description",""),command=data.get("command"),status="pending")
    db.add(s); db.commit(); db.refresh(s); return obj_to_dict(s)

@app.put("/api/v1/redteam/executions/{exec_id}/steps/{step_id}")
def update_step(exec_id:int,step_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    s=db.query(AttackStep).filter(AttackStep.id==step_id,AttackStep.execution_id==exec_id).first()
    if not s: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(s,k): setattr(s,k,v)
    db.commit(); return obj_to_dict(s)

@app.get("/api/v1/redteam/recon")
def list_recon(page:int=1,size:int=20,type:Optional[str]=None,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(ReconRecord)
    if type: q=q.filter(ReconRecord.type==type)
    if search: q=q.filter(ReconRecord.target.ilike(f"%{search}%"))
    return paginate(q.order_by(desc(ReconRecord.created_at)),page,size)

@app.post("/api/v1/redteam/recon")
def add_recon(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=ReconRecord(target=data["target"],type=data.get("type","osint"),data=data.get("data",{}),source=data.get("source","manual"))
    db.add(r); db.commit(); db.refresh(r); return obj_to_dict(r)

@app.get("/api/v1/redteam/payloads")
def list_payloads(page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(Payload).order_by(Payload.id),page,size)

@app.post("/api/v1/redteam/payloads")
def add_payload(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    p=Payload(name=data["name"],type=data.get("type","exploit"),description=data.get("description",""),platform=data.get("platform","all"),mitre_techniques=data.get("mitre_techniques",[]),is_active=True,created_by_id=current_user.id)
    db.add(p); db.commit(); db.refresh(p); return obj_to_dict(p)

@app.get("/api/v1/redteam/stats")
def redteam_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    execs=db.query(AttackExecution).all()
    avg_dr=sum(e.detection_rate for e in execs)/len(execs) if execs else 0
    return {"plans":db.query(AttackPlan).count(),"active_executions":db.query(AttackExecution).filter(AttackExecution.status.in_(["running","pending"])).count(),"completed_executions":db.query(AttackExecution).filter(AttackExecution.status=="completed").count(),"techniques_tested":db.query(AttackStep.technique_id).distinct().count(),"detection_rate":round(avg_dr*100,1),"steps_total":db.query(AttackStep).count(),"steps_detected":db.query(AttackStep).filter(AttackStep.detection_triggered==True).count()}

# Blue Team
@app.get("/api/v1/blueteam/hunting-queries")
def list_hunting_queries(page:int=1,size:int=20,search:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(ThreatHuntingQuery)
    if search: q=q.filter(or_(ThreatHuntingQuery.name.ilike(f"%{search}%"),ThreatHuntingQuery.description.ilike(f"%{search}%")))
    return paginate(q.order_by(ThreatHuntingQuery.id),page,size)

@app.post("/api/v1/blueteam/hunting-queries")
def create_hunting_query(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    hq=ThreatHuntingQuery(name=data["name"],description=data.get("description",""),query=data.get("query",""),data_source=data.get("data_source","logs"),tags=data.get("tags",[]),mitre_techniques=data.get("mitre_techniques",[]),created_by_id=current_user.id)
    db.add(hq); db.commit(); db.refresh(hq); return obj_to_dict(hq)

@app.put("/api/v1/blueteam/hunting-queries/{query_id}")
def update_hunting_query(query_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    hq=db.query(ThreatHuntingQuery).filter(ThreatHuntingQuery.id==query_id).first()
    if not hq: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(hq,k): setattr(hq,k,v)
    db.commit(); return obj_to_dict(hq)

@app.post("/api/v1/blueteam/hunting-queries/{query_id}/run")
def run_hunting_query(query_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    hq=db.query(ThreatHuntingQuery).filter(ThreatHuntingQuery.id==query_id).first()
    if not hq: raise HTTPException(404,"Not found")
    hq.last_run=datetime.utcnow(); hq.results_count=random.randint(0,50); db.commit()
    results=[{"timestamp":(datetime.utcnow()-timedelta(minutes=i*10)).isoformat(),"asset":f"asset-{random.randint(1,10)}","user":"corp\\user","detail":f"Match #{i+1}"} for i in range(min(hq.results_count,10))]
    return {"query_id":query_id,"results_count":hq.results_count,"results":results}

@app.get("/api/v1/blueteam/edr-events")
def list_edr_events(page:int=1,size:int=50,event_type:Optional[str]=None,severity:Optional[str]=None,blocked:Optional[bool]=None,asset_id:Optional[int]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(EDREvent)
    if event_type: q=q.filter(EDREvent.event_type==event_type)
    if severity: q=q.filter(EDREvent.severity==AlertSeverity(severity))
    if blocked is not None: q=q.filter(EDREvent.blocked==blocked)
    if asset_id: q=q.filter(EDREvent.asset_id==asset_id)
    return paginate(q.order_by(desc(EDREvent.timestamp)),page,size)

@app.post("/api/v1/blueteam/edr-events")
def ingest_edr_event(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ev=EDREvent(asset_id=data.get("asset_id"),event_type=data.get("event_type","process"),severity=AlertSeverity(data.get("severity","info")),process_name=data.get("process_name"),command_line=data.get("command_line"),username=data.get("username"),details=data.get("details",{}))
    db.add(ev); db.commit(); db.refresh(ev); return obj_to_dict(ev)

@app.get("/api/v1/blueteam/fim")
def list_fim(page:int=1,size:int=20,status:Optional[str]=None,asset_id:Optional[int]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(FIMRecord)
    if status: q=q.filter(FIMRecord.status==status)
    if asset_id: q=q.filter(FIMRecord.asset_id==asset_id)
    return paginate(q.order_by(desc(FIMRecord.checked_at)),page,size)

@app.get("/api/v1/blueteam/stats")
def blueteam_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    now=datetime.utcnow(); today_start=now.replace(hour=0,minute=0,second=0)
    return {"hunting_queries":db.query(ThreatHuntingQuery).count(),"edr_events_today":db.query(EDREvent).filter(EDREvent.timestamp>=today_start).count(),"edr_blocked_today":db.query(EDREvent).filter(EDREvent.timestamp>=today_start,EDREvent.blocked==True).count(),"fim_alerts":db.query(FIMRecord).filter(FIMRecord.status.in_(["suspicious","modified"])).count(),"rules_active":db.query(DetectionRule).filter(DetectionRule.enabled==True).count(),"edr_by_type":{t:db.query(EDREvent).filter(EDREvent.event_type==t).count() for t in ["process","file","network","registry","memory","dns","wmi"]}}

# Purple Team
@app.get("/api/v1/purpleteam/exercises")
def list_exercises(page:int=1,size:int=20,status:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Exercise)
    if status: q=q.filter(Exercise.status==status)
    return paginate(q.order_by(desc(Exercise.created_at)),page,size)

@app.post("/api/v1/purpleteam/exercises")
def create_exercise(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ex=Exercise(name=data["name"],description=data.get("description",""),type=data.get("type","tabletop"),status="planned",red_team=data.get("red_team",[]),blue_team=data.get("blue_team",[]),objectives=data.get("objectives",[]),scope=data.get("scope",""),mitre_tactics=data.get("mitre_tactics",[]),start_date=datetime.utcnow())
    db.add(ex); db.commit(); db.refresh(ex); return obj_to_dict(ex)

@app.get("/api/v1/purpleteam/exercises/{ex_id}")
def get_exercise(ex_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ex=db.query(Exercise).filter(Exercise.id==ex_id).first()
    if not ex: raise HTTPException(404,"Not found")
    d=obj_to_dict(ex); d["steps"]=[obj_to_dict(s) for s in db.query(ExerciseStep).filter(ExerciseStep.exercise_id==ex_id).order_by(ExerciseStep.step_order).all()]; return d

@app.put("/api/v1/purpleteam/exercises/{ex_id}")
def update_exercise(ex_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    ex=db.query(Exercise).filter(Exercise.id==ex_id).first()
    if not ex: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(ex,k): setattr(ex,k,v)
    db.commit(); return obj_to_dict(ex)

@app.post("/api/v1/purpleteam/exercises/{ex_id}/steps")
def add_exercise_step(ex_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    s=ExerciseStep(exercise_id=ex_id,technique_id=data.get("technique_id","T1000"),step_order=data.get("step_order",1),red_action=data.get("red_action",""),blue_expected=data.get("blue_expected",""))
    db.add(s); db.commit(); db.refresh(s); return obj_to_dict(s)

@app.put("/api/v1/purpleteam/exercises/{ex_id}/steps/{step_id}")
def update_exercise_step(ex_id:int,step_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    s=db.query(ExerciseStep).filter(ExerciseStep.id==step_id,ExerciseStep.exercise_id==ex_id).first()
    if not s: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(s,k): setattr(s,k,v)
    db.commit()
    ex=db.query(Exercise).filter(Exercise.id==ex_id).first()
    steps=db.query(ExerciseStep).filter(ExerciseStep.exercise_id==ex_id,ExerciseStep.detection_success.isnot(None)).all()
    if steps and ex:
        ex.detection_rate=sum(1 for st in steps if st.detection_success)/len(steps)
    db.commit(); return obj_to_dict(s)

@app.get("/api/v1/purpleteam/coverage")
def list_coverage(tactic_id:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    results=db.query(ATTACKCoverage).all(); items=[]
    for cov in results:
        d=obj_to_dict(cov)
        tech=db.query(MITRETechnique).filter(MITRETechnique.technique_id==cov.technique_id).first()
        if tech:
            d["technique_name"]=tech.name; d["tactic_ids"]=tech.tactic_ids
            if tactic_id and tactic_id not in (tech.tactic_ids or []): continue
        items.append(d)
    return {"items":items,"total":len(items)}

@app.get("/api/v1/purpleteam/coverage/matrix")
def coverage_matrix(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    tactics=db.query(MITRETactic).all(); techniques=db.query(MITRETechnique).all()
    coverage={c.technique_id:c for c in db.query(ATTACKCoverage).all()}; matrix={}
    for tactic in tactics:
        tactic_techs=[t for t in techniques if tactic.tactic_id in (t.tactic_ids or [])]
        matrix[tactic.tactic_id]={"tactic":obj_to_dict(tactic),"techniques":[{**obj_to_dict(t),"coverage":obj_to_dict(coverage.get(t.technique_id))} for t in tactic_techs]}
    return matrix

@app.put("/api/v1/purpleteam/coverage/{technique_id}")
def update_coverage(technique_id:str,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    cov=db.query(ATTACKCoverage).filter(ATTACKCoverage.technique_id==technique_id).first()
    if not cov: cov=ATTACKCoverage(technique_id=technique_id); db.add(cov)
    for k,v in data.items():
        if hasattr(cov,k): setattr(cov,k,v)
    db.commit(); return obj_to_dict(cov)

@app.get("/api/v1/purpleteam/stats")
def purpleteam_stats(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    total=db.query(ATTACKCoverage).count(); covered=db.query(ATTACKCoverage).filter(ATTACKCoverage.covered==True).count()
    exercises=db.query(Exercise).all(); avg_dr=sum(e.detection_rate for e in exercises)/len(exercises) if exercises else 0
    return {"exercises_total":len(exercises),"exercises_completed":sum(1 for e in exercises if e.status=="completed"),"coverage_percentage":round(covered/total*100,1) if total else 0,"avg_detection_rate":round(avg_dr*100,1),"techniques_total":total,"techniques_covered":covered}

# MITRE
@app.get("/api/v1/mitre/tactics")
def list_tactics(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(t) for t in db.query(MITRETactic).order_by(MITRETactic.tactic_id).all()]

@app.get("/api/v1/mitre/techniques")
def list_techniques(tactic_id:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    techniques=db.query(MITRETechnique).all()
    if tactic_id: techniques=[t for t in techniques if tactic_id in (t.tactic_ids or [])]
    return [obj_to_dict(t) for t in techniques]

@app.get("/api/v1/mitre/techniques/{technique_id}")
def get_technique(technique_id:str,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    t=db.query(MITRETechnique).filter(MITRETechnique.technique_id==technique_id).first()
    if not t: raise HTTPException(404,"Not found")
    d=obj_to_dict(t); d["coverage"]=obj_to_dict(db.query(ATTACKCoverage).filter(ATTACKCoverage.technique_id==technique_id).first()); return d

# Playbooks
@app.get("/api/v1/playbooks")
def list_playbooks(page:int=1,size:int=20,type:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(Playbook)
    if type: q=q.filter(Playbook.type==type)
    return paginate(q.order_by(Playbook.id),page,size)

@app.post("/api/v1/playbooks")
def create_playbook(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    pb=Playbook(name=data["name"],description=data.get("description",""),type=data.get("type","incident_response"),tags=data.get("tags",[]),mitre_techniques=data.get("mitre_techniques",[]),steps_json=data.get("steps",[]),estimated_minutes=data.get("estimated_minutes"),created_by_id=current_user.id)
    db.add(pb); db.commit(); db.refresh(pb); return obj_to_dict(pb)

@app.get("/api/v1/playbooks/{pb_id}")
def get_playbook(pb_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    pb=db.query(Playbook).filter(Playbook.id==pb_id).first()
    if not pb: raise HTTPException(404,"Not found")
    return obj_to_dict(pb)

@app.put("/api/v1/playbooks/{pb_id}")
def update_playbook(pb_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    pb=db.query(Playbook).filter(Playbook.id==pb_id).first()
    if not pb: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if k=="steps": pb.steps_json=v
        elif hasattr(pb,k): setattr(pb,k,v)
    db.commit(); return obj_to_dict(pb)

@app.post("/api/v1/playbooks/{pb_id}/execute")
def execute_playbook(pb_id:int,data:dict=Body(default={}),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    pb=db.query(Playbook).filter(Playbook.id==pb_id).first()
    if not pb: raise HTTPException(404,"Not found")
    pe=PlaybookExecution(playbook_id=pb_id,incident_id=data.get("incident_id"),status="running",current_step=0,notes=data.get("notes",""))
    db.add(pe); db.commit(); db.refresh(pe); return obj_to_dict(pe)

@app.get("/api/v1/playbooks/executions")
def list_pb_executions(page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(PlaybookExecution).order_by(desc(PlaybookExecution.started_at)),page,size)

@app.get("/api/v1/playbooks/executions/{pe_id}")
def get_pb_execution(pe_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    pe=db.query(PlaybookExecution).filter(PlaybookExecution.id==pe_id).first()
    if not pe: raise HTTPException(404,"Not found")
    d=obj_to_dict(pe); pb=db.query(Playbook).filter(Playbook.id==pe.playbook_id).first(); d["playbook"]=obj_to_dict(pb); return d

@app.put("/api/v1/playbooks/executions/{pe_id}/step")
def advance_step(pe_id:int,data:dict=Body(default={}),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    pe=db.query(PlaybookExecution).filter(PlaybookExecution.id==pe_id).first()
    if not pe: raise HTTPException(404,"Not found")
    pb=db.query(Playbook).filter(Playbook.id==pe.playbook_id).first()
    pe.current_step+=1
    if pb and pe.current_step>=len(pb.steps_json or []): pe.status="completed"; pe.completed_at=datetime.utcnow()
    db.commit(); return obj_to_dict(pe)

# Compliance
@app.get("/api/v1/compliance/frameworks")
def list_frameworks(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    results=[]
    for fw in db.query(ComplianceFramework).all():
        d=obj_to_dict(fw); total=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id).count()
        compliant=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="compliant").count()
        partial=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="partial").count()
        non_compliant=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="non_compliant").count()
        d["assessment_stats"]={"total":total,"compliant":compliant,"partial":partial,"non_compliant":non_compliant,"score":round(compliant/total*100,1) if total else 0}
        results.append(d)
    return results

@app.get("/api/v1/compliance/frameworks/{fw_id}/controls")
def list_framework_controls(fw_id:int,page:int=1,size:int=50,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(ComplianceControl).filter(ComplianceControl.framework_id==fw_id).order_by(ComplianceControl.control_id),page,size)

@app.get("/api/v1/compliance/assessments")
def list_assessments(page:int=1,size:int=20,framework_id:Optional[int]=None,status:Optional[str]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(ComplianceAssessment)
    if framework_id: q=q.filter(ComplianceAssessment.framework_id==framework_id)
    if status: q=q.filter(ComplianceAssessment.status==status)
    result=paginate(q.order_by(ComplianceAssessment.id),page,size)
    for item in result["items"]:
        ctrl=db.query(ComplianceControl).filter(ComplianceControl.id==item["control_id"]).first()
        if ctrl:
            item["control_name"]=ctrl.name; item["control_ref"]=ctrl.control_id
            fw=db.query(ComplianceFramework).filter(ComplianceFramework.id==ctrl.framework_id).first()
            if fw: item["framework_name"]=fw.name
    return result

@app.post("/api/v1/compliance/assessments")
def create_assessment(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    a=ComplianceAssessment(framework_id=data["framework_id"],control_id=data["control_id"],asset_id=data.get("asset_id"),status=data.get("status","not_assessed"),notes=data.get("notes",""),evidence=data.get("evidence",[]),assessed_by_id=current_user.id,assessed_at=datetime.utcnow())
    db.add(a); db.commit(); db.refresh(a); return obj_to_dict(a)

@app.put("/api/v1/compliance/assessments/{assess_id}")
def update_assessment(assess_id:int,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    a=db.query(ComplianceAssessment).filter(ComplianceAssessment.id==assess_id).first()
    if not a: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(a,k): setattr(a,k,v)
    a.assessed_by_id=current_user.id; a.assessed_at=datetime.utcnow()
    db.commit(); return obj_to_dict(a)

@app.get("/api/v1/compliance/score")
def compliance_score(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    results=[]
    for fw in db.query(ComplianceFramework).all():
        total=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id).count()
        compliant=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="compliant").count()
        partial=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="partial").count()
        non_compliant=db.query(ComplianceAssessment).filter(ComplianceAssessment.framework_id==fw.id,ComplianceAssessment.status=="non_compliant").count()
        score=round(((compliant+partial*0.5)/total)*100,1) if total else 0
        results.append({"name":fw.name,"score":score,"compliant":compliant,"partial":partial,"non_compliant":non_compliant,"total":total})
    return {"by_framework":results,"overall":round(sum(r["score"] for r in results)/len(results),1) if results else 0}

# Reports
@app.get("/api/v1/reports/templates")
def list_report_templates(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(t) for t in db.query(ReportTemplate).all()]

@app.post("/api/v1/reports/templates")
def create_report_template(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    t=ReportTemplate(name=data["name"],type=data.get("type","technical"),description=data.get("description",""),sections=data.get("sections",[]))
    db.add(t); db.commit(); db.refresh(t); return obj_to_dict(t)

@app.get("/api/v1/reports")
def list_reports(page:int=1,size:int=20,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return paginate(db.query(GeneratedReport).order_by(desc(GeneratedReport.created_at)),page,size)

@app.post("/api/v1/reports/generate")
def generate_report(data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    r=GeneratedReport(template_id=data.get("template_id"),name=data.get("name","Generated Report"),type=data.get("type","technical"),created_by_id=current_user.id,format=data.get("format","pdf"),status="completed")
    db.add(r); db.commit(); db.refresh(r); return obj_to_dict(r)

@app.delete("/api/v1/reports/{report_id}")
def delete_report(report_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    r=db.query(GeneratedReport).filter(GeneratedReport.id==report_id).first()
    if not r: raise HTTPException(404,"Not found")
    db.delete(r); db.commit(); return {"message":"Report deleted"}

# Notifications
@app.get("/api/v1/notifications/channels")
def list_channels(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [obj_to_dict(c) for c in db.query(NotificationChannel).all()]

@app.post("/api/v1/notifications/channels")
def create_channel(data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=NotificationChannel(name=data["name"],type=data.get("type","webhook"),config=data.get("config",{}),enabled=data.get("enabled",True))
    db.add(c); db.commit(); db.refresh(c); return obj_to_dict(c)

@app.put("/api/v1/notifications/channels/{ch_id}")
def update_channel(ch_id:int,data:dict=Body(...),db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=db.query(NotificationChannel).filter(NotificationChannel.id==ch_id).first()
    if not c: raise HTTPException(404,"Not found")
    for k,v in data.items():
        if hasattr(c,k): setattr(c,k,v)
    db.commit(); return obj_to_dict(c)

@app.post("/api/v1/notifications/channels/{ch_id}/test")
def test_channel(ch_id:int,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    c=db.query(NotificationChannel).filter(NotificationChannel.id==ch_id).first()
    if not c: raise HTTPException(404,"Not found")
    c.last_test_at=datetime.utcnow(); c.last_test_success=True; db.commit()
    return {"message":f"Test sent to {c.name}","success":True}

# Audit
@app.get("/api/v1/audit/logs")
def list_audit_logs(page:int=1,size:int=50,action:Optional[str]=None,resource_type:Optional[str]=None,user_id:Optional[int]=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    q=db.query(AuditLog)
    if action: q=q.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type: q=q.filter(AuditLog.resource_type==resource_type)
    if user_id: q=q.filter(AuditLog.user_id==user_id)
    return paginate(q.order_by(desc(AuditLog.timestamp)),page,size)

# Settings
@app.get("/api/v1/settings")
def get_settings(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    settings=db.query(SystemSetting).all(); by_cat={}
    for s in settings:
        if s.category not in by_cat: by_cat[s.category]=[]
        by_cat[s.category].append(obj_to_dict(s))
    return by_cat

@app.put("/api/v1/settings/{key}")
def update_setting(key:str,data:dict=Body(...),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.admin: raise HTTPException(403,"Admin required")
    s=db.query(SystemSetting).filter(SystemSetting.key==key).first()
    if not s: raise HTTPException(404,"Setting not found")
    s.value=data.get("value"); db.commit(); return obj_to_dict(s)

# Platform
@app.get("/api/v1/platform/health")
def platform_health(db:Session=Depends(get_db)):
    try:
        db.query(User).count(); db_ok=True
    except: db_ok=False
    return {"status":"healthy" if db_ok else "degraded","version":"2.0.0","database":"ok" if db_ok else "error","timestamp":datetime.utcnow().isoformat(),"uptime_seconds":86400,"stats":{"users":db.query(User).count() if db_ok else 0,"assets":db.query(Asset).count() if db_ok else 0,"alerts":db.query(Alert).count() if db_ok else 0}}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db, SessionLocal
from .models import User, Customer, LoanApplication, Document, AuditLog, Notification
from .schemas import LoginIn, RegisterIn, CustomerIn, ApplicationIn, DocumentIn, StatusIn, ReviewIn, NotifyIn
from .security import hash_password, verify_password, token_for, current_user
from .services import calculate_risk, underwriting_brief

app = FastAPI(title="Credora AI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)

def audit(db, user, action, entity, entity_id, details=""):
    db.add(AuditLog(actor=user.email, action=action, entity=entity, entity_id=str(entity_id), details=details))
    db.commit()

def seed():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email=="admin@credora.ai").first():
            db.add(User(name="Credora Admin", email="admin@credora.ai",
                        password_hash=hash_password("Admin@123"), role="admin"))
            db.commit()
    finally: db.close()
seed()

def customer_dict(c):
    return {"id":c.id,"full_name":c.full_name,"email":c.email,"phone":c.phone,
            "annual_income":c.annual_income,"employment_type":c.employment_type,
            "kyc_status":c.kyc_status,"created_at":c.created_at}

def app_dict(a):
    return {"id":a.id,"customer_id":a.customer_id,"customer_name":a.customer.full_name,
            "product":a.product,"amount":a.amount,"tenure_months":a.tenure_months,"purpose":a.purpose,
            "status":a.status,"credit_score":a.credit_score,"monthly_debt":a.monthly_debt,
            "risk_score":a.risk_score,"risk_band":a.risk_band,"ai_summary":a.ai_summary,
            "reviewer_note":a.reviewer_note,"human_approved":a.human_approved,"created_at":a.created_at}

@app.get("/api/health")
def health(): return {"status":"ok","service":"Credora AI"}

@app.post("/api/auth/register")
def register(data:RegisterIn, db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,"Email already registered")
    u=User(name=data.name,email=data.email,password_hash=hash_password(data.password),role=data.role)
    db.add(u); db.commit(); db.refresh(u)
    return {"access_token":token_for(u),"token_type":"bearer","user":{"name":u.name,"email":u.email,"role":u.role}}

@app.post("/api/auth/login")
def login(data:LoginIn, db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"access_token":token_for(u),"token_type":"bearer","user":{"name":u.name,"email":u.email,"role":u.role}}

@app.get("/api/me")
def me(u=Depends(current_user)): return {"name":u.name,"email":u.email,"role":u.role}

@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db), u=Depends(current_user)):
    apps=db.query(LoanApplication).all()
    return {"customers":db.query(Customer).count(),"applications":len(apps),
            "approved":sum(a.status=="Approved" for a in apps),
            "under_review":sum(a.status in ["Submitted","Under Review","More Info Required"] for a in apps),
            "high_risk":sum(a.risk_band=="High" for a in apps),
            "total_requested":sum(a.amount for a in apps),
            "recent":[app_dict(a) for a in sorted(apps,key=lambda x:x.created_at,reverse=True)[:5]]}

@app.get("/api/customers")
def customers(db:Session=Depends(get_db), u=Depends(current_user)):
    return [customer_dict(c) for c in db.query(Customer).order_by(Customer.id.desc()).all()]

@app.post("/api/customers")
def create_customer(data:CustomerIn, db:Session=Depends(get_db), u=Depends(current_user)):
    c=Customer(**data.model_dump()); db.add(c); db.commit(); db.refresh(c); audit(db,u,"CREATE","Customer",c.id)
    return customer_dict(c)

@app.patch("/api/customers/{cid}/kyc")
def set_kyc(cid:int,data:StatusIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(Customer,cid)
    if not c: raise HTTPException(404,"Customer not found")
    c.kyc_status=data.status; db.commit(); audit(db,u,"KYC_UPDATE","Customer",cid,data.status)
    return customer_dict(c)

@app.get("/api/applications")
def applications(db:Session=Depends(get_db),u=Depends(current_user)):
    return [app_dict(a) for a in db.query(LoanApplication).order_by(LoanApplication.id.desc()).all()]

@app.post("/api/applications")
def create_application(data:ApplicationIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if not db.get(Customer,data.customer_id): raise HTTPException(404,"Customer not found")
    a=LoanApplication(**data.model_dump()); db.add(a); db.commit(); db.refresh(a)
    audit(db,u,"CREATE","Application",a.id,f"₹{a.amount}")
    return app_dict(a)

@app.get("/api/applications/{aid}")
def application(aid:int,db:Session=Depends(get_db),u=Depends(current_user)):
    a=db.get(LoanApplication,aid)
    if not a: raise HTTPException(404,"Application not found")
    out=app_dict(a); out["documents"]=[{"id":d.id,"document_type":d.document_type,"file_name":d.file_name,
        "verification_status":d.verification_status,"extracted_summary":d.extracted_summary} for d in a.documents]
    return out

@app.post("/api/documents")
def add_document(data:DocumentIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if not db.get(LoanApplication,data.application_id): raise HTTPException(404,"Application not found")
    d=Document(**data.model_dump()); db.add(d); db.commit(); db.refresh(d); audit(db,u,"CREATE","Document",d.id,data.document_type)
    return {"id":d.id,"document_type":d.document_type,"file_name":d.file_name,"verification_status":d.verification_status}

@app.patch("/api/documents/{did}/verify")
def verify_doc(did:int,data:StatusIn,db:Session=Depends(get_db),u=Depends(current_user)):
    d=db.get(Document,did)
    if not d: raise HTTPException(404,"Document not found")
    d.verification_status=data.status; db.commit(); audit(db,u,"VERIFY","Document",did,data.status)
    return {"id":d.id,"verification_status":d.verification_status}

@app.post("/api/risk/{aid}")
def run_risk(aid:int,db:Session=Depends(get_db),u=Depends(current_user)):
    a=db.get(LoanApplication,aid)
    if not a: raise HTTPException(404,"Application not found")
    score,band,reasons,missing=calculate_risk(a,a.customer,a.documents)
    a.risk_score=score; a.risk_band=band; a.status="Under Review"; db.commit()
    audit(db,u,"RISK_ANALYSIS","Application",aid,f"{band}:{score}")
    return {"risk_score":score,"risk_band":band,"reasons":reasons,"missing_documents":missing}

@app.post("/api/underwriting/{aid}/brief")
def brief(aid:int,db:Session=Depends(get_db),u=Depends(current_user)):
    a=db.get(LoanApplication,aid)
    if not a: raise HTTPException(404,"Application not found")
    a.ai_summary=underwriting_brief(a,a.customer,a.documents); db.commit()
    audit(db,u,"AI_BRIEF","Application",aid)
    return {"summary":a.ai_summary}

@app.post("/api/underwriting/{aid}/review")
def review(aid:int,data:ReviewIn,db:Session=Depends(get_db),u=Depends(current_user)):
    a=db.get(LoanApplication,aid)
    if not a: raise HTTPException(404,"Application not found")
    allowed={"approve":"Approved","reject":"Rejected","request_info":"More Info Required"}
    if data.decision not in allowed: raise HTTPException(400,"Invalid decision")
    a.status=allowed[data.decision]; a.reviewer_note=data.note; a.human_approved=data.decision=="approve"; db.commit()
    audit(db,u,"HUMAN_REVIEW","Application",aid,f"{a.status}: {data.note}")
    return app_dict(a)

@app.post("/api/notifications/{aid}")
def notify(aid:int,data:NotifyIn,db:Session=Depends(get_db),u=Depends(current_user)):
    a=db.get(LoanApplication,aid)
    if not a: raise HTTPException(404,"Application not found")
    msg=data.message or f"Your {a.product} application #{a.id} is now {a.status}."
    n=Notification(application_id=aid,channel=data.channel,recipient=a.customer.email,message=msg,status="Sent (Demo)")
    db.add(n); db.commit(); audit(db,u,"NOTIFY","Application",aid,data.channel)
    return {"recipient":n.recipient,"channel":n.channel,"message":n.message,"status":n.status}

@app.get("/api/audit")
def logs(db:Session=Depends(get_db),u=Depends(current_user)):
    return [{"id":x.id,"actor":x.actor,"action":x.action,"entity":x.entity,"entity_id":x.entity_id,
             "details":x.details,"created_at":x.created_at} for x in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()]

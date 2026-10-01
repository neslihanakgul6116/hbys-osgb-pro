from datetime import datetime
import hashlib
import os
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI(
    title="Enterprise OSGB & Hastane Bilgi Sistemi (HBYS) Ultimate Pro",
    version="7.1 - Tam Donanımlı HBYS (Röntgen Aktif)",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- VERİTABANI (SQLALCHEMY) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./checkup.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- TABLOLAR ---
class PatientModel(Base):
  __tablename__ = "patients"
  id = Column(Integer, primary_key=True, index=True)
  tc = Column(String, unique=True, index=True)
  name = Column(String)
  phone = Column(String)
  department = Column(String)
  created_at = Column(DateTime, default=datetime.utcnow)


class PrescriptionModel(Base):
  __tablename__ = "prescriptions"
  id = Column(Integer, primary_key=True, index=True)
  employee_id = Column(Integer)
  drug_name = Column(String)
  instructions = Column(String)
  erecete_no = Column(String, unique=True)
  created_at = Column(DateTime, default=datetime.utcnow)


class RadiologyModel(Base):
  __tablename__ = "radiology"
  id = Column(Integer, primary_key=True, index=True)
  tc = Column(String)
  modality = Column(String)
  body_part = Column(String)
  status = Column(String, default="PACS Arşivine Yüklendi")
  created_at = Column(DateTime, default=datetime.utcnow)


class LabModel(Base):
  __tablename__ = "lab_results"
  id = Column(Integer, primary_key=True, index=True)
  tc = Column(String)
  test_name = Column(String)
  result_value = Column(String)
  status = Column(String, default="Normal")
  created_at = Column(DateTime, default=datetime.utcnow)


class BedModel(Base):
  __tablename__ = "beds"
  id = Column(Integer, primary_key=True, index=True)
  ward_name = Column(String)
  bed_number = Column(String)
  status = Column(String, default="Boş")
  patient_tc = Column(String, nullable=True)


class AuditLogModel(Base):
  __tablename__ = "audit_logs"
  id = Column(Integer, primary_key=True, index=True)
  timestamp = Column(String)
  user = Column(String)
  category = Column(String)
  detail = Column(String)
  ip = Column(String)


Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


def log_audit(
    db: Session, user: str, category: str, detail: str, ip: str = "127.0.0.1"
):
  log_entry = AuditLogModel(
      timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      user=user,
      category=category,
      detail=detail,
      ip=ip,
  )
  db.add(log_entry)
  db.commit()


# --- KULLANICI & ROL YÖNETİMİ (RBAC) ---
USERS_DB = {
    "admin@hastane.com": {
        "password": "guvenlisifre123",
        "role": "admin",
        "name": "Sistem Admin",
    },
    "doktor@hastane.com": {
        "password": "guvenlisifre123",
        "role": "doctor",
        "name": "Dr. Hasan YILMAZ",
    },
    "radyolog@hastane.com": {
        "password": "guvenlisifre123",
        "role": "radiologist",
        "name": "Uzm. Dr. Can Demir",
    },
    "laboratuvar@hastane.com": {
        "password": "guvenlisifre123",
        "role": "lab",
        "name": "Biyokimyager Cemil",
    },
}


def get_current_user_role(token: str = Depends(oauth2_scheme)):
  for email, data in USERS_DB.items():
    expected_token = hashlib.sha256(email.encode()).hexdigest()
    if token == expected_token:
      return {"email": email, "role": data["role"], "name": data["name"]}
  raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Geçersiz veya süresi dolmuş token!",
  )


# --- PYDANTIC ŞEMALARI ---
class PatientCreate(BaseModel):
  tc: str
  name: str
  phone: str
  department: str


class PrescriptionCreate(BaseModel):
  employee_id: int
  drug_name: str
  instructions: str


class RadiologyCreate(BaseModel):
  tc: str
  modality: str
  body_part: str


class LabCreate(BaseModel):
  tc: str
  test_name: str
  result_value: str
  status: str


class BedAssign(BaseModel):
  ward_name: str
  bed_number: str
  patient_tc: str


# --- GİRİŞ ENDPOINT ---
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
  user = USERS_DB.get(form_data.username)
  if not user or user["password"] != form_data.password:
    raise HTTPException(
        status_code=400, detail="Hatalı kullanıcı adı veya şifre"
    )
  token = hashlib.sha256(form_data.username.encode()).hexdigest()
  return {
      "access_token": token,
      "token_type": "bearer",
      "role": user["role"],
      "name": user["name"],
  }


# --- API ENDPOINTS ---
@app.post("/api/patients")
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] not in ["admin", "doctor"]:
    raise HTTPException(
        status_code=403, detail="Bu işlem için yetkiniz yok (Yetkisiz Rol)."
    )
  existing = db.query(PatientModel).filter(PatientModel.tc == patient.tc).first()
  if existing:
    raise HTTPException(
        status_code=400, detail="Bu TC Kimlik numarasına ait hasta zaten kayıtlı!"
    )
  db_patient = PatientModel(
      tc=patient.tc,
      name=patient.name,
      phone=patient.phone,
      department=patient.department,
  )
  db.add(db_patient)
  db.commit()
  log_audit(
      db, current_user["email"], "PATIENT_CREATE", f"Yeni hasta: {patient.tc}"
  )
  return {"status": "success", "message": "Hasta kalıcı veritabanına kaydedildi."}


@app.get("/api/patients")
async def get_patients(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  patients = db.query(PatientModel).all()
  return {
      "status": "success",
      "patients": [
          {
              "tc": p.tc,
              "name": p.name,
              "phone": p.phone,
              "department": p.department,
          }
          for p in patients
      ],
  }


# --- RÖNTGEN & MR ENDPOINT'LERİ (AKTİF EDİLDİ) ---
@app.post("/api/radiology")
async def create_radiology_request(
    rad: RadiologyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] not in ["admin", "doctor", "radiologist"]:
    raise HTTPException(
        status_code=403, detail="Röntgen/MR istemi için yetkiniz bulunmuyor."
    )

  db_rad = RadiologyModel(
      tc=rad.tc,
      modality=rad.modality,
      body_part=rad.body_part,
      status="PACS Arşivine Yüklendi",
  )
  db.add(db_rad)
  db.commit()
  log_audit(
      db,
      current_user["email"],
      "RADIOLOGY_REQ",
      f"{rad.modality} çekimi istendi: {rad.body_part} (TC: {rad.tc})",
  )
  return {
      "status": "success",
      "message": f"{rad.modality} istemi PACS sistemine aktarıldı.",
  }


@app.get("/api/radiology")
async def get_radiology_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  items = (
      db.query(RadiologyModel).order_by(RadiologyModel.id.desc()).all()
  )
  return {
      "status": "success",
      "records": [
          {
              "tc": r.tc,
              "modality": r.modality,
              "body_part": r.body_part,
              "status": r.status,
              "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
          }
          for r in items
      ],
  }


@app.post("/api/lab")
async def create_lab_result(
    lab: LabCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] not in ["admin", "doctor", "lab"]:
    raise HTTPException(
        status_code=403, detail="Laboratuvar sonuç girişi için yetkiniz yok."
    )
  db_lab = LabModel(
      tc=lab.tc,
      test_name=lab.test_name,
      result_value=lab.result_value,
      status=lab.status,
  )
  db.add(db_lab)
  db.commit()
  log_audit(
      db,
      current_user["email"],
      "LAB_RESULT",
      f"Lab Sonucu Eklendi: {lab.test_name} ({lab.status})",
  )
  return {"status": "success", "message": "LIS laboratuvar sonucu işlendi."}


@app.get("/api/lab")
async def get_lab_results(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  items = db.query(LabModel).order_by(LabModel.id.desc()).all()
  return {
      "status": "success",
      "records": [
          {
              "tc": r.tc,
              "test_name": r.test_name,
              "result_value": r.result_value,
              "status": r.status,
              "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
          }
          for r in items
      ],
  }


@app.post("/api/beds/assign")
async def assign_bed(
    bed_data: BedAssign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] not in ["admin", "doctor"]:
    raise HTTPException(
        status_code=403, detail="Yatak atama yetkiniz bulunmuyor."
    )
  db_bed = (
      db.query(BedModel)
      .filter(
          BedModel.ward_name == bed_data.ward_name,
          BedModel.bed_number == bed_data.bed_number,
      )
      .first()
  )
  if not db_bed:
    db_bed = BedModel(
        ward_name=bed_data.ward_name,
        bed_number=bed_data.bed_number,
        status="Dolu",
        patient_tc=bed_data.patient_tc,
    )
    db.add(db_bed)
  else:
    db_bed.status = "Dolu"
    db_bed.patient_tc = bed_data.patient_tc
  db.commit()
  log_audit(
      db,
      current_user["email"],
      "BED_ASSIGN",
      f"Yatak Atandı: {bed_data.ward_name} No:{bed_data.bed_number} -> Hasta:"
      f" {bed_data.patient_tc}",
  )
  return {"status": "success", "message": "Yatak doluluk durumu güncellendi."}


@app.get("/api/beds")
async def get_beds(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  beds = db.query(BedModel).all()
  return {
      "status": "success",
      "beds": [
          {
              "ward_name": b.ward_name,
              "bed_number": b.bed_number,
              "status": b.status,
              "patient_tc": b.patient_tc,
          }
          for b in beds
      ],
  }


@app.get("/api/export/enabiz-fhir")
async def export_enabiz_fhir(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] != "admin":
    raise HTTPException(
        status_code=403,
        detail="Bakanlık FHIR veri dışa aktarımı sadece Admin yetkisindedir.",
    )

  patients = db.query(PatientModel).all()
  xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<Bundle xmlns="http://hl7.org/fhir">\n  <type value="collection"/>\n'
  for p in patients:
    xml_content += f'  <entry>\n    <patientTC>{p.tc}</patientTC>\n    <patientName>{p.name}</patientName>\n    <department>{p.department}</department>\n  </entry>\n'
  xml_content += "</Bundle>"

  log_audit(
      db,
      current_user["email"],
      "FHIR_EXPORT",
      "Sağlık Bakanlığı E-Nabız FHIR XML toplu dışa aktarımı yapıldı.",
  )
  return Response(
      content=xml_content,
      media_type="application/xml",
      headers={
          "Content-Disposition": "attachment;filename=enabiz_fhir_export.xml"
      },
  )


@app.get("/api/audit-logs")
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_role),
):
  if current_user["role"] != "admin":
    raise HTTPException(
        status_code=403,
        detail="KVKK uyarınca Audit loglarını sadece Admin görebilir!",
    )
  logs = (
      db.query(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(20).all()
  )
  return {
      "status": "success",
      "logs": [
          {
              "timestamp": l.timestamp,
              "user": l.user,
              "category": l.category,
              "detail": l.detail,
              "ip": l.ip,
          }
          for l in logs
      ],
  }


# --- ANA SAYFA ---
@app.get("/", response_class=HTMLResponse)
async def root():
  index_path = os.path.join("templates", "index.html")
  if os.path.exists(index_path):
    return FileResponse(index_path)
  return "<h3>index.html bulunamadı!</h3>"
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Bilgisayarında otomatik oluşacak veritabanı dosyası
SQLALCHEMY_DATABASE_URL = "sqlite:///./checkup.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 1. Şirketler Tablosu
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True)
    tax_number = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 2. Kullanıcılar Tablosu (İK, Doktor, Çalışan, Admin)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # 'admin', 'hr_manager', 'doctor', 'employee'

# 3. Randevular Tablosu
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"))
    appointment_time = Column(DateTime)
    status = Column(String, default="pending") # pending, confirmed, completed

# 4. Tıbbi Sonuçlar Tablosu (🔒 KVKK Hassas Alan)
class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    lab_results_json = Column(Text) 
    doctor_notes = Column(Text) 
    status_for_hr = Column(String) # 'fit_to_work' veya 'requires_followup'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Veritabanı tablolarını oluşturan komut
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Veritabanı ve tablolar başarıyla oluşturuldu!")
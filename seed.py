from database import SessionLocal, Company, User

# Veritabanı oturumunu başlat
db = SessionLocal()

print("Test verileri ekleniyor...")

# 1. Örnek bir şirket ekleyelim
sample_company = Company(company_name="Anadolu Tekstil A.Ş.", tax_number="1234567890")
db.add(sample_company)
db.commit() # Veritabanına kaydet
db.refresh(sample_company) # Oluşan ID'yi almak için yenile

print(f"Şirket eklendi: {sample_company.company_name} (ID: {sample_company.id})")

# 2. Şirkete ait bir İK Yöneticisi ekleyelim
hr_user = User(
    company_id=sample_company.id,
    full_name="Ayşe İK Uzmanı",
    email="ayse@anadolu.com",
    password_hash="sifre123", # Normalde şifrelenir, şimdilik basit tutuyoruz
    role="hr_manager"
)

# 3. Bir İş Yeri Hekimi (Doktor) ekleyelim (Doktorlar şirkete bağlı olmak zorunda değil)
doctor_user = User(
    company_id=None,
    full_name="Dr. Mehmet Hekim",
    email="mehmet@saglik.com",
    password_hash="sifre123",
    role="doctor"
)

db.add(hr_user)
db.add(doctor_user)
db.commit()

print("Örnek kullanıcılar (İK ve Doktor) başarıyla eklendi!")
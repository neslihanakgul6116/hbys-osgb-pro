# Enterprise OSGB & HBYS v7.0

Bu proje, hastaneler ve Ortak Sağlık Güvenlik Birimleri (OSGB) için geliştirilmiş modern, hafif ve taşınabilir bir Hastane Bilgi Yönetim Sistemi (HBYS) çözümüdür.

## 🚀 Özellikler
- **Personel Girişi & JWT Tabanlı Yetkilendirme (RBAC)**
- **Hasta Kayıt ve Otomatik Barkod Üretimi**
- **Laboratuvar Bilgi Sistemi (LIS) ve Yatak/Servis Yönetimi**
- **Radyoloji (PACS / EMR) Entegrasyonu**
- **KVKK Uyumlu Denetim Günlükleri (Audit Logs)**
- **Sağlık Bakanlığı e-Nabız için FHIR / XML Dışa Aktarım**

## 💻 Kurulum ve Çalıştırma (venv Olmadan)

Projeyi bilgisayarınıza indirdikten sonra proje klasöründe terminali açın ve şu adımları takip edin:

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic
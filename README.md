# Hunter Mail Found — Email Hunt Backend

Şirket adlarından yola çıkıp domain'lerini çözümleyen ve bu domain'lerden
herkese açık kaynaklarla email toplayan n-tier backend servisi.

## Mimari (n-tier)

```
app/
├── api/v1/          # Sunum katmanı — FastAPI router'ları
├── schemas/         # Pydantic DTO'lar (katmanlar arası sözleşme)
├── services/        # İş katmanı
│   ├── hunt_service.py      # tarama orkestrasyonu
│   ├── hunt_runner.py       # arka plan görevi
│   ├── domain_resolver.py   # Tavily ile şirket → domain
│   ├── email_verifier.py    # sözdizimi + MX doğrulama
│   ├── export_service.py    # BCC / CSV üretimi
│   └── sources/             # email kaynakları (hunter, crtsh, contact_page, tavily)
├── repositories/    # Veri erişim katmanı
├── models/          # SQLAlchemy ORM varlıkları
├── db/              # SQLite engine + seed
└── core/            # ayarlar (.env) + logging
```

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`.env` dosyasına anahtarları yazın (yer tutucu bırakılırsa ilgili kaynak
sessizce devre dışı kalır, API ayağa kalkmaya devam eder):

```
TAVILY_API_KEY=...
HUNTER_API_KEY=...
```

## Çalıştırma

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- SQLite dosyası (`hunter.db`) ilk açılışta otomatik oluşur ve eski
  `COMPANY_NAMES` listesi kategori/şirket olarak seed edilir.

## Email kaynakları

| Kaynak        | Maliyet           | Açıklama                                                          |
|---------------|-------------------|-------------------------------------------------------------------|
| `crtsh`       | ücretsiz          | Certificate Transparency kayıtlarındaki emailler                  |
| `contact_page`| ücretsiz          | site iletişim sayfalarındaki `mailto:` ve metin içi adresler      |
| `tavily`      | Tavily kredisi    | web arama sonuç içeriklerinden `@domain` adresi ayıklama          |
| `hunter`      | Hunter kredisi    | Hunter.io domain-search (ad, pozisyon, güven skoru ile)           |

Varsayılan kaynak seti kredi harcamaz: `["crtsh", "contact_page", "tavily"]`.
Hunter'ı isteğe bağlı açın: `POST /api/v1/hunt/run` gövdesinde `"use_hunter": true`.

## Önemli endpoint'ler

```bash
# Şirketleri listele
curl "http://127.0.0.1:8000/api/v1/companies"

# Manuel şirket ekle (domain biliniyorsa ver — Tavily çağrısını atlar)
curl -X POST http://127.0.0.1:8000/api/v1/companies \
  -H "Content-Type: application/json" \
  -d '{"name": "OBSS", "category": "Kurumsal Yazilim & Bilisim", "domain": "obss.com.tr"}'

# Taramayı başlat (arka planda çalışır)
curl -X POST http://127.0.0.1:8000/api/v1/hunt/run \
  -H "Content-Type: application/json" \
  -d '{"companies": ["OBSS"], "sources": ["crtsh", "contact_page"]}'

# Oturum durumu
curl http://127.0.0.1:8000/api/v1/hunt/sessions/1

# Bulunan emailler
curl "http://127.0.0.1:8000/api/v1/emails?category=Kurumsal%20Yazilim%20%26%20Bilisim"

# BCC listesi indir (geçersiz + sistem adresleri hariç)
curl -OJ "http://127.0.0.1:8000/api/v1/exports/bcc"

# Hunter kalan kredi
curl http://127.0.0.1:8000/api/v1/hunt/credits/hunter
```

## Güven skoru ve doğrulama

- Kaynak bazlı taban puan: hunter 90, contact_page 70, crtsh 55, tavily 50.
- Aynı adres birden çok kaynaktan geldiyse kaynak başına +5 bonus.
- MX/sözdizimi doğrulaması geçen adrese +10; geçemeyen `invalid` işaretlenir.
- `noreply` vb. sistem adresleri `type=system` olarak işaretlenir ve BCC
  listesinden çıkarılır (`include_system=true` ile geri eklenir).

## Yasal not

Toplu e-posta gönderimi Türkiye'de KVKK ve ticari elektronik ileti (İYS)
mevzuatına tabi olabilir. Bu araç yalnızca herkese açık kaynaklardan veri
toplar; toplu gönderim kararları ve yükümlülükleri kullanıcınındır.

## Yol haritası (faz 2)

- Email permütasyon (`first.last@`, `flast@` …) + SMTP mailbox probe
  (`py3-validate-email`)
- Hunter `email-finder` / `email-verifier` endpoint'leri
- Zamanlanmış yeniden tarama + yeni adres delta raporu
- CSV/Excel dışa aktarım çeşitleri

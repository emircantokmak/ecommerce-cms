# Django REST Framework E-Ticaret API

Django 6.1 ve Django REST Framework ile geliştirilmiş, JWT kimlik doğrulaması kullanan e-ticaret API projesidir. Mevcut uygulama; kullanıcı kaydı/e-posta doğrulama, ürün ve kategori yönetimi, Supabase Storage görsel yükleme, favoriler, sepet, filtreleme, Redis/yerel bellek önbelleği ve e-posta bildirimlerini içerir.

> **Güvenlik notu:** Gerçek `.env` dosyası depoya veya ZIP paketine eklenmemelidir. Daha önce Git'e eklenmiş gerçek anahtarlar varsa yalnızca `.gitignore` eklemek yeterli değildir; ilgili anahtarları Supabase/e-posta sağlayıcısında yenileyin ve Git geçmişinden temizleyin.

## 1. Teknolojiler

- Python 3.12+
- Django 6.1
- Django REST Framework
- Simple JWT
- django-filter
- SQLite (varsayılan) veya yapılandırılabilir veritabanı
- Redis (opsiyonel önbellek)
- Supabase Storage (ürün görselleri)
- SMTP / Django e-posta backend'i
- Docker ve Docker Compose

## 2. Projeyi yerel ortamda çalıştırma

### 2.1. Depoyu indirin ve sanal ortam oluşturun

```bash
git clone <DEPO_ADRESI>
cd drf
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2.2. Bağımlılıkları kurun

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3. Ortam değişkenlerini hazırlayın

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

`.env` dosyasını açıp kendi değerlerinizi girin. `DJANGO_SECRET_KEY` için uzun, rastgele ve başka yerde kullanılmayan bir anahtar üretin. Geliştirme ortamında e-posta backend'i varsayılan olarak konsola yazar; SMTP ile gerçek e-posta göndermek için `EMAIL_BACKEND` ve SMTP alanlarını yapılandırın.

### 2.4. Veritabanını hazırlayın

```bash
python manage.py migrate
```

İsteğe bağlı yönetici hesabı:

```bash
python manage.py createsuperuser
```

### 2.5. Sunucuyu başlatın

```bash
python manage.py runserver
```

API varsayılan olarak `http://127.0.0.1:8000/api/` adresindedir. Django yönetim paneli `http://127.0.0.1:8000/admin/` adresindedir.

## 3. Ortam değişkenleri

| Değişken | Açıklama |
|---|---|
| `DJANGO_ENV` | `development` veya `production` |
| `DJANGO_SECRET_KEY` | Django gizli anahtarı; production'da zorunludur |
| `DJANGO_DEBUG` | Geliştirme için `True`, production için `False` |
| `DJANGO_ALLOWED_HOSTS` | Virgülle ayrılmış host listesi |
| `TIME_ZONE` | Varsayılan `Europe/Istanbul` |
| `SQLITE_PATH` | SQLite dosya yolu |
| `REDIS_URL` | Örn. `redis://127.0.0.1:6379/1`; boşsa LocMemCache |
| `EMAIL_BACKEND` | Geliştirmede console, production'da SMTP backend |
| `EMAIL_HOST` | SMTP sunucusu; Gmail için `smtp.gmail.com` |
| `EMAIL_PORT` | TLS için genellikle `587`, SSL için `465` |
| `EMAIL_USE_TLS` | STARTTLS kullanımı |
| `EMAIL_USE_SSL` | SSL kullanımı; TLS ile aynı anda açmayın |
| `EMAIL_HOST_USER` | SMTP kullanıcı/e-posta adresi |
| `EMAIL_HOST_PASSWORD` | SMTP uygulama parolası veya sağlayıcı parolası |
| `DEFAULT_FROM_EMAIL` | Gönderen adresi |
| `EMAIL_TIMEOUT` | SMTP zaman aşımı (saniye) |
| `SUPABASE_URL` | Supabase proje URL'si |
| `SUPABASE_SECRET_KEY` | Sunucu tarafında saklanması gereken Supabase gizli anahtarı |
| `SUPABASE_BUCKET_NAME` | Görsel bucket adı; varsayılan `product-images` |
| `CORS_ALLOW_ALL_ORIGINS` | Yalnızca kontrollü geliştirme ortamında `True` |
| `CORS_ALLOWED_ORIGINS` | Virgülle ayrılmış frontend origin listesi |

### Gmail SMTP örneği

Google hesabınızda iki aşamalı doğrulamayı açıp bir uygulama şifresi oluşturun. Normal hesap parolanızı `.env` içine yazmayın.

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=ornek@gmail.com
EMAIL_HOST_PASSWORD=google-uygulama-sifresi
DEFAULT_FROM_EMAIL=E-Ticaret <ornek@gmail.com>
EMAIL_TIMEOUT=15
```

SMTP sağlayıcısının gönderim limiti ve doğrulama kuralları geçerlidir. Üretimde SPF, DKIM ve DMARC kayıtlarını da yapılandırın.

## 4. E-posta sistemi

Tüm e-posta gönderimleri `api/email_service.py` üzerinden yapılır. Böylece konu, gövde, gönderen, hata yakalama ve loglama tek noktadan yönetilir. Doğrulama ve ürün bildirimlerinde Türkçe HTML şablonları kullanılır; düz metin alternatifi de gönderilir.

### 4.1. Gönderilen bildirimler

| Olay | Alıcı | İçerik |
|---|---|---|
| Kayıt | Yeni e-posta adresi | 24 saat geçerli hesap doğrulama bağlantısı |
| Ürün oluşturma | İşlemi yapan kullanıcının e-postası | Ürünün oluşturulduğu |
| Ürün güncelleme | İşlemi yapan kullanıcının e-postası | Ürünün güncellendiği |
| Ürün silme | İşlemi yapan kullanıcının e-postası | Ürünün silindiği |
| E-posta değiştirme | Eski ve yeni e-posta adresleri | E-posta değişikliği güvenlik bildirimi |
| Kullanıcı adı değiştirme | Kullanıcının kayıtlı e-postası | Yeni kullanıcı adı bildirimi |
| Şifre değiştirme | Kullanıcının kayıtlı e-postası | Şifrenin değiştiği; yeni şifre paylaşılmaz |
| Hesap silme | Silme öncesindeki kayıtlı e-posta | Hesabın silindiği |

E-posta gönderimi başarısız olursa hata loglanır; ürün veya hesap işleminin veritabanındaki sonucu SMTP arızası nedeniyle geri alınmaz. E-posta gönderiminin başarılı olması, alıcının iletiyi gelen kutusunda gördüğünü garanti etmez.

### 4.2. E-posta doğrulama akışı

1. `POST /api/user/register/` kullanıcıyı `is_active=False` olarak oluşturur.
2. İmzalı doğrulama token'ı oluşturulur ve e-posta ile gönderilir.
3. Kullanıcı `GET /api/user/verify-email/?token=...` adresini açar.
4. Token imzası ve 24 saatlik geçerlilik süresi kontrol edilir.
5. Doğrulama başarılıysa hesap etkinleştirilir.
6. Etkin olmayan kullanıcı giriş yapmaya çalışırsa `403` döndürülür.

### 4.3. E-posta güvenliği

- Şifre veya token e-posta bildirimlerine yazılmaz (doğrulama bağlantısı hariç).
- Şifre değiştirme, e-posta değiştirme, kullanıcı adı değiştirme ve hesap silme işlemleri mevcut şifre doğrulaması ister.
- E-posta değişikliğinde eski ve yeni adres bilgilendirilir.
- E-posta gönderim hataları uygulama loglarına yazılır; hassas kimlik bilgileri loglanmaz.
- Daha ileri production kullanımı için SMTP gönderimini Celery/RQ gibi bir kuyruk sistemine taşımak önerilir.

## 5. API uç noktaları

Tüm yollar `/api/` önekiyle kullanılır. JWT gerektiren uç noktalarda istek başlığı:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 5.1. Kullanıcı ve kimlik doğrulama

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `POST` | `/api/user/register/` | Herkes | Kullanıcı kaydı ve doğrulama e-postası |
| `GET` | `/api/user/verify-email/?token=...` | Herkes | E-posta doğrulama |
| `POST` | `/api/user/login/` | Herkes | Kullanıcı adı/şifre ile JWT üretimi |
| `GET` | `/api/user/profile/` | Giriş gerekli | Profil bilgileri |
| `PATCH` | `/api/user/profile/` | Giriş + mevcut şifre | Kullanıcı adı/e-posta profil güncellemesi |
| `POST` | `/api/user/change-email/` | Giriş + mevcut şifre | E-posta değiştirme; `new_email_confirm` zorunlu |
| `POST` | `/api/user/change-username/` | Giriş + mevcut şifre | Kullanıcı adı değiştirme |
| `POST` | `/api/user/change-password/` | Giriş + mevcut şifre | Şifre değiştirme |
| `DELETE` | `/api/user/account/` | Giriş + mevcut şifre | Hesabı silme; JSON gövdesinde `current_password` |

Kayıt örneği:

```json
{
  "username": "ornek_kullanici",
  "email": "kullanici@example.com",
  "password": "GucluBirSifre123!"
}
```

E-posta değiştirme örneği:

```json
{
  "current_password": "MevcutSifre123!",
  "new_email": "yeni@example.com",
  "new_email_confirm": "yeni@example.com"
}
```

Şifre değiştirme örneği:

```json
{
  "current_password": "MevcutSifre123!",
  "new_password": "YeniGucluSifre456!"
}
```

Hesap silme örneği (`DELETE` isteğinin JSON gövdesi):

```json
{
  "current_password": "MevcutSifre123!"
}
```

### 5.2. Kategoriler

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `GET` | `/api/categories/` | Herkes | Kategorileri listeler |
| `POST` | `/api/categories/` | Admin | Kategori oluşturur |
| `GET` | `/api/categories/<category_id>/` | Herkes | Kategori detayı |
| `PUT/PATCH` | `/api/categories/<category_id>/` | Admin | Kategori günceller |
| `DELETE` | `/api/categories/<category_id>/` | Admin | Kategori siler |

### 5.3. Ürünler

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `GET` | `/api/products/` | Herkes | Aktif ürünleri sayfalı listeler |
| `GET` | `/api/products/<product_id>/` | Herkes | Aktif ürün detayı |
| `GET` | `/api/products/featured/` | Herkes | Öne çıkan aktif ürünler |
| `POST` | `/api/products/featured/` | Admin | Öne çıkan ürün oluşturur |
| `PUT/PATCH` | `/api/products/featured/<product_id>/` | Admin | Öne çıkan ürünü günceller |
| `DELETE` | `/api/products/featured/<product_id>/` | Admin | Ürünü öne çıkan listesinden kaldırır |
| `GET` | `/api/user/products/` | Giriş gerekli | Kullanıcının ürünleri |
| `POST` | `/api/user/products/` | Giriş gerekli | Ürün oluşturur ve e-posta bildirimi gönderir |
| `PUT/PATCH` | `/api/user/products/<product_id>/` | Ürün sahibi | Ürünü günceller ve e-posta bildirimi gönderir |
| `DELETE` | `/api/user/products/<product_id>/` | Ürün sahibi | Ürünü siler ve e-posta bildirimi gönderir |

Ürün listeleme filtreleri:

- `search`: Başlık ve açıklamada arama.
- `category`: Kategori slug değeri.
- `min_price`: En düşük fiyat.
- `max_price`: En yüksek fiyat.
- `ordering`: `price`, `-price`, `created_at`, `-created_at`, `title`, `-title`.
- `page`: Sayfa numarası. Sayfa başına 5 ürün.
- Ürün fiyatı API doğrulamasında sıfırdan büyük olmalıdır.

Örnek:

```http
GET /api/products/?search=telefon&min_price=1000&max_price=30000&ordering=-price&page=1
```

### 5.4. Ürün görselleri

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `GET` | `/api/user/products/<product_id>/images/` | Ürün sahibi | Görselleri listeler |
| `POST` | `/api/user/products/<product_id>/images/` | Ürün sahibi | Supabase Storage'a görsel yükler |
| `PATCH` | `/api/user/products/<product_id>/images/<image_id>/` | Ürün sahibi | Görsel bilgilerini günceller |
| `DELETE` | `/api/user/products/<product_id>/images/<image_id>/` | Ürün sahibi | Görseli ve Storage nesnesini siler |

Yükleme `multipart/form-data` ile yapılır. İzin verilen içerik tipleri JPEG, PNG ve WebP'dir. Yükleme için Supabase URL, gizli anahtar ve bucket ayarları gereklidir.

### 5.5. Favoriler

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `GET` | `/api/favorites/` | Giriş gerekli | Kullanıcının favorileri |
| `POST` | `/api/favorites/<product_id>/` | Giriş gerekli | Aktif ürünü favorilere ekler |
| `DELETE` | `/api/favorites/<product_id>/` | Giriş gerekli | Favoriden çıkarır |

### 5.6. Sepet

| Method | Endpoint | Yetki | Açıklama |
|---|---|---|---|
| `GET` | `/api/cart/` | Giriş gerekli | Sepeti getirir; yoksa oluşturur |
| `POST` | `/api/cart/` | Giriş gerekli | Ürünü sepete ekler |
| `POST` | `/api/cart/items/` | Giriş gerekli | Sepet kalemi ekleme (mevcut route) |
| `PATCH` | `/api/cart/items/<item_id>/` | Sepet sahibi | Miktarı günceller |
| `DELETE` | `/api/cart/items/<item_id>/` | Sepet sahibi | Sepet kalemini siler |

Sepet ekleme gövdesi:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

Stok miktarını aşan veya sıfır/negatif miktarlar kabul edilmez. Aynı ürün tekrar eklenirse mevcut miktara eklenir.

## 6. Önbellek

Ürün listeleme yanıtları URL/sorgu parametrelerine göre anahtarlanan 60 saniyelik cache ile saklanır. `REDIS_URL` tanımlanırsa Redis, tanımlanmazsa Django LocMemCache kullanılır. Ürün oluşturma, güncelleme ve silme işlemlerinde mevcut cache temizlenir.

Redis'i yerel çalıştırmak için:

```bash
docker run --name drf-redis -p 6379:6379 -d redis:7-alpine
```

`.env`:

```env
REDIS_URL=redis://127.0.0.1:6379/1
```

## 7. Testler

Tüm API testleri:

```bash
python manage.py test api
```

Ayrıntılı çıktı:

```bash
python manage.py test api --verbosity 2
```

Django yapılandırma kontrolü:

```bash
python manage.py check
```

Testler; JWT girişi, kategori yetkilendirmesi ve CRUD, ürün yetkilendirmesi/filtreleme/sıralama/cache, öne çıkan ürün yönetimi, favoriler, sepet, görsel yükleme, e-posta doğrulama ve hesap/ürün e-posta bildirimlerini kapsar. E-posta testlerinde gerçek SMTP sunucusu kullanılmaz; Django'nun bellek içi e-posta backend'i kullanılır.

## 8. Docker ile çalıştırma

Önce `.env.example` dosyasını `.env` olarak kopyalayıp düzenleyin. Ardından:

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
```

Loglar:

```bash
docker compose logs -f web
```

Durdurmak:

```bash
docker compose down
```

Compose yapılandırması web servisi ve Redis servisini başlatır. SQLite dosyası Docker volume üzerinde tutulur. Production'da SQLite yerine PostgreSQL gibi yönetilen bir veritabanı kullanılması tavsiye edilir.

## 9. Production kontrol listesi

- [ ] `DJANGO_ENV=production` ve `DJANGO_DEBUG=False`.
- [ ] Güçlü ve gizli `DJANGO_SECRET_KEY`.
- [ ] Gerçek domainler `DJANGO_ALLOWED_HOSTS` içinde.
- [ ] CORS yalnızca bilinen frontend origin'lerine açık.
- [ ] HTTPS ve güvenli cookie ayarları aktif.
- [ ] SMTP kimlik bilgileri secret manager/ortam değişkenlerinde.
- [ ] Supabase gizli anahtarı yalnızca backend'de.
- [ ] Supabase bucket erişim politikaları kontrol edilmiş.
- [ ] PostgreSQL yedekleme ve migration stratejisi hazırlanmış.
- [ ] Redis erişimi dış dünyaya kapalı ve parola/ağ politikasıyla korunuyor.
- [ ] Uygulama Gunicorn ve reverse proxy arkasında çalışıyor; `runserver` production'da kullanılmıyor.
- [ ] E-posta domain SPF, DKIM ve DMARC kayıtları tanımlı.
- [ ] Log, hata izleme, rate limit, yedekleme ve izleme sistemi kurulmuş.
- [ ] Git geçmişinde `.env`, veritabanı, `venv` ve kullanıcı verisi bulunmuyor.

## 10. Bilinen kapsam sınırları

Bu depo mevcut uygulamanın API kapsamını ve burada açıklanan bildirimleri sağlar. Ödeme sağlayıcısı entegrasyonu, sipariş/teslimat/iade akışları, stok rezervasyonu, kuyruk tabanlı e-posta, gelişmiş rate limiting ve kapsamlı audit log mevcut API kapsamının dışında olup ayrı geliştirme gerektirir. Production'a çıkmadan önce bu iş alanlarının gereksinimleri ayrıca tamamlanmalıdır.

## 11. Lisans ve katkı

Bu proje için lisans belirtilmemiştir. Dağıtım veya ticari kullanım öncesinde uygun lisans ekleyin. Geliştirme önerileri için issue/branch/pull request akışını kullanın.

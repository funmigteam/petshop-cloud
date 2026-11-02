<div align="center">

# 🐾 Pet Online
### Online storefronts and QR catalogs for pet shops

**A Persian-first, multi-shop catalog platform built with Django.** Give every pet shop a polished public page, an easy product manager, and a QR code customers can scan in-store.

[فارسی](#فارسی) · [English](#english)

</div>

---

## فارسی

### معرفی

**پت آنلاین** بستری برای ساخت کاتالوگ دیجیتال پت‌شاپ‌هاست. هر فروشگاه صفحه عمومی و QR اختصاصی خودش را دارد؛ مشتری‌ها محصولات را دسته‌بندی‌شده و بدون قیمت می‌بینند و مدیر فروشگاه از پنل ساده، محتوا و اشتراک را مدیریت می‌کند.

### امکانات

- 🏪 صفحه اختصاصی هر پت‌شاپ با لوگو، بنر، اطلاعات تماس، آدرس و رنگ برند
- 🧭 صفحه اصلی با جست‌وجوی فروشگاه، شهر و محصول، به‌علاوه نقشه فروشگاه‌ها
- 🐕 مدیریت محصولات، تصاویر، دسته‌بندی‌ها، موجودی و پیشنهادهای ویژه
- 📱 QR اختصاصی برای هر فروشگاه؛ خروجی PNG و نسخه چاپی A5
- 🛠️ پنل مدیریت مرکزی برای فروشگاه‌ها، پلن‌ها، اشتراک‌ها، پرداخت‌ها و درخواست عضویت
- 💳 پرداخت اشتراک با جیبیت؛ درگاه آزمایشی داخلی برای توسعه و راه‌اندازی اولیه
- 🔐 ورود مدیر فروشگاه با رمز یا لینک پنل اختصاصی قابل ابطال
- 🎨 رابط راست‌چین فارسی با فونت وزیرمتن و دارایی‌های محلی

### پیش‌نیازها

- Python 3.10 یا بالاتر
- pip
- کلیدهای جیبیت فقط برای پرداخت واقعی (اختیاری)

### راه‌اندازی محلی

```bash
git clone https://github.com/funmigteam/petshop-cloud.git
cd petshop-cloud
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_site
python manage.py createsuperuser
python manage.py runserver
```

سایت در `http://127.0.0.1:8000/` اجرا می‌شود. مسیرهای پرکاربرد:

| مسیر | کاربرد |
|---|---|
| `/` | صفحه عمومی و فهرست فروشگاه‌ها |
| `/join/` | درخواست عضویت فروشگاه |
| `/map/` | نقشه فروشگاه‌ها |
| `/login/` | ورود |
| `/panel/` | پنل فروشگاه |
| `/manage/` | پنل مدیریت مرکزی |
| `/django-admin/` | پنل پیش‌فرض Django |

برای ساخت داده نمونه (اختیاری):

```bash
python manage.py seed_demo
```

این دستور چهار فروشگاه نمونه با رمز `demo1234` می‌سازد؛ فقط برای محیط توسعه استفاده شود.

### تنظیمات محیطی

تنظیمات از متغیر محیطی خوانده می‌شوند. مقادیر پیش‌فرض برای توسعه محلی هستند؛ در سرور واقعی حتماً کلید محرمانه و میزبان‌ها را تنظیم کنید.

| متغیر | توضیح |
|---|---|
| `DJANGO_SECRET_KEY` | کلید محرمانه Django؛ در production تصادفی و محرمانه باشد |
| `DJANGO_DEBUG` | حالت توسعه؛ در production برابر `0` قرار دهید |
| `DJANGO_ALLOWED_HOSTS` | نام میزبان‌ها، جداشده با کاما |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | مبدأهای HTTPS مورد اعتماد CSRF |
| `SITE_URL` | نشانی کامل سایت؛ برای QR و بازگشت پرداخت استفاده می‌شود |
| `JIBIT_API_KEY` و `JIBIT_SECRET_KEY` | کلیدهای درگاه جیبیت؛ بدون آن‌ها درگاه آزمایشی فعال است |
| `JIBIT_MOCK` | فعال‌سازی صریح درگاه آزمایشی (`1` یا `0`) |
| `JIBIT_BASE_URL` | نشانی API جیبیت (اختیاری؛ پیش‌فرض در تنظیمات پروژه) |
| `JIBIT_TIMEOUT` | مهلت درخواست‌های API بر حسب ثانیه |
| `SERVE_FILES` | سرو فایل‌های static و media با Django؛ پشت وب‌سرور معمولاً خاموش باشد |
| `MAP_TILE_URL` | الگوی آدرس tile نقشه؛ پیش‌فرض OpenStreetMap |
| `MAP_TILE_ATTRIBUTION` | متن انتساب ارائه‌دهنده tile |
| `MAP_DEFAULT_LAT` و `MAP_DEFAULT_LNG` | مرکز پیش‌فرض نقشه |

نمونه برای محیط production:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
SITE_URL=https://example.com
JIBIT_API_KEY=your-api-key
JIBIT_SECRET_KEY=your-secret-key
```

### انتشار در production

1. متغیرهای محیطی بالا را تنظیم کنید و `DEBUG` را خاموش نگه دارید.
2. مهاجرت‌ها و فایل‌های static را آماده کنید:

   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

3. برنامه را با یک WSGI server مانند Gunicorn اجرا و پشت Nginx یا reverse proxy مشابه قرار دهید.
4. وب‌سرور باید `/static/` را از `staticfiles/` و `/media/` را از مسیر media سرو کند. از پشتیبان‌گیری امن دیتابیس و فایل‌های آپلودی مطمئن شوید.
5. برای پرداخت واقعی، نشانی HTTPS سایت را در تنظیمات جیبیت و `SITE_URL` ثبت کنید.

> پایگاه داده پیش‌فرض SQLite است و برای توسعه محلی مناسب است. برای بار کاری production، پایگاه داده و شیوه پشتیبان‌گیری متناسب با زیرساخت خود را انتخاب کنید.

### فناوری‌ها

`Python` · `Django 5.2` · `SQLite` · `Pillow` · `Requests` · `Leaflet` · `OpenStreetMap`

### ساختار پروژه

```text
core/                  مدل‌ها، فرم‌ها، سرویس پرداخت، QR و viewها
  management/commands/ دستورات setup_site و seed_demo
  views/               بخش عمومی، احراز هویت، پنل فروشگاه و مدیریت
petshop_cloud/         تنظیمات و پیکربندی اصلی Django
templates/             قالب‌های فارسی و راست‌چین
static/                CSS، JavaScript، فونت وزیرمتن و لوگو
media/                 فایل‌های آپلودی کاربران (محلی؛ در Git نگهداری نمی‌شود)
```

---

## English

### Overview

**Pet Online** is a Persian-first platform for digital pet-shop catalogs. Each shop gets a public storefront and a unique QR code. Customers can browse categorized products without prices, while shop owners manage their catalog and subscription from a dedicated dashboard.

### Features

- 🏪 Branded storefronts with logo, banner, contact details, address, and theme color
- 🧭 Searchable directory by shop, city, and product, plus a shops map
- 🐕 Product, image, category, availability, and featured-item management
- 📱 Per-shop QR codes with PNG download and print-ready A5 page
- 🛠️ Central admin dashboard for shops, plans, subscriptions, payments, and join requests
- 💳 Jibit subscription payments with a built-in mock gateway for development
- 🔐 Password sign-in and revocable shop-specific panel links
- 🎨 Persian RTL interface with locally hosted Vazirmatn fonts and assets

### Requirements

- Python 3.10+
- pip
- Jibit credentials for real payments (optional)

### Local setup

```bash
git clone https://github.com/funmigteam/petshop-cloud.git
cd petshop-cloud
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_site
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Useful routes:

| Route | Purpose |
|---|---|
| `/` | Public directory and storefront discovery |
| `/join/` | Shop registration request |
| `/map/` | Shop map |
| `/login/` | Sign in |
| `/panel/` | Shop dashboard |
| `/manage/` | Central management dashboard |
| `/django-admin/` | Django admin |

Optional demo data:

```bash
python manage.py seed_demo
```

This creates four sample shops with the password `demo1234`. Use this command only in a development environment.

### Environment variables

Settings are read from environment variables. Defaults are intended for local development; configure a secret key and allowed hosts before deploying.

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key; use a long, private value in production |
| `DJANGO_DEBUG` | Development mode; set to `0` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Trusted HTTPS origins for CSRF |
| `SITE_URL` | Full public URL, used for QR codes and payment callbacks |
| `JIBIT_API_KEY`, `JIBIT_SECRET_KEY` | Jibit credentials; the mock gateway is used when credentials are absent |
| `JIBIT_MOCK` | Explicitly enable (`1`) or disable (`0`) the mock gateway |
| `JIBIT_BASE_URL` | Jibit API base URL (optional; project default applies) |
| `JIBIT_TIMEOUT` | API request timeout in seconds |
| `SERVE_FILES` | Let Django serve static and media files; usually disabled behind a web server |
| `MAP_TILE_URL` | Map tile URL template; defaults to OpenStreetMap |
| `MAP_TILE_ATTRIBUTION` | Map tile provider attribution text |
| `MAP_DEFAULT_LAT`, `MAP_DEFAULT_LNG` | Default map center coordinates |

Example production configuration:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
SITE_URL=https://example.com
JIBIT_API_KEY=your-api-key
JIBIT_SECRET_KEY=your-secret-key
```

### Production deployment

1. Configure the environment variables above and keep `DEBUG` disabled.
2. Apply migrations and collect static assets:

   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

3. Run the app with a WSGI server such as Gunicorn behind Nginx or a similar reverse proxy.
4. Serve `/static/` from `staticfiles/` and `/media/` from the media directory. Back up the database and uploaded files securely.
5. Use HTTPS and register the public callback URL with Jibit for real payments.

> SQLite is configured by default and is convenient for local development. Choose a production database and backup strategy that fit your deployment.

### Tech stack

`Python` · `Django 5.2` · `SQLite` · `Pillow` · `Requests` · `Leaflet` · `OpenStreetMap`

### Project layout

```text
core/                  Models, forms, payment client, QR renderer, and views
  management/commands/ setup_site and seed_demo commands
  views/               Public pages, auth, shop dashboard, and management
petshop_cloud/         Django project settings and entry points
templates/             Persian RTL templates
static/                CSS, JavaScript, Vazirmatn fonts, and logo
media/                 User uploads (local only; excluded from Git)
```

---

<div align="center">
Made with 🐾 for pet shops and their people
</div>

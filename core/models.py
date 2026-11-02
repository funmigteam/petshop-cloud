import secrets
import uuid
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image, ImageOps

from .icons import PET_ICONS


def new_panel_token():
    return secrets.token_urlsafe(24)


def new_reference():
    return uuid.uuid4().hex


def shrink_image(field, max_side):
    if not field or getattr(field, "_committed", True):
        return
    img = Image.open(field)
    img = ImageOps.exif_transpose(img)
    has_alpha = img.mode in ("RGBA", "LA", "P")
    img = img.convert("RGBA" if has_alpha else "RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = BytesIO()
    if has_alpha:
        img.save(buf, "PNG", optimize=True)
        ext = "png"
    else:
        img.save(buf, "JPEG", quality=85, optimize=True, progressive=True)
        ext = "jpg"
    name = f"{uuid.uuid4().hex[:16]}.{ext}"
    field.save(name, ContentFile(buf.getvalue()), save=False)


hex_color = RegexValidator(r"^#[0-9a-fA-F]{6}$", "رنگ باید به شکل #RRGGBB باشد.")


class SiteConfig(models.Model):

    hero_title = models.CharField("تیتر صفحه اصلی", max_length=120, default="پت شاپ‌های شهرت، یک‌جا")
    hero_subtitle = models.CharField(
        "زیرتیتر", max_length=255, default="کاتالوگ آنلاین پت شاپ‌ها با منوی QR — غذا، لوازم و اکسسوری حیوانات خانگی"
    )
    support_phone = models.CharField("تلفن پشتیبانی", max_length=30, blank=True, default="09993397299")
    about = models.TextField("درباره ما", blank=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ShopQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_active=True, subscription_until__gt=timezone.now())


class Shop(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop", verbose_name="مالک")
    name = models.CharField("نام پت شاپ", max_length=100)
    slug = models.SlugField(
        "آدرس اختصاصی (انگلیسی)", max_length=60, unique=True,
        help_text="فقط حروف انگلیسی، عدد و خط تیره. مثال: pet-house",
    )
    tagline = models.CharField("شعار کوتاه", max_length=140, blank=True)
    description = models.TextField("معرفی", blank=True)
    logo = models.ImageField("لوگو", upload_to="shops/logos/", blank=True)
    banner = models.ImageField("بنر", upload_to="shops/banners/", blank=True)
    theme_color = models.CharField("رنگ اصلی", max_length=7, default="#0d9488", validators=[hex_color])
    phone = models.CharField("تلفن", max_length=30, blank=True)
    address = models.CharField("آدرس", max_length=255, blank=True)
    city = models.CharField("شهر", max_length=50, blank=True)
    working_hours = models.CharField("ساعات کاری", max_length=100, blank=True)
    instagram = models.CharField("اینستاگرام", max_length=60, blank=True, help_text="فقط نام کاربری، بدون @")

    lat = models.DecimalField("عرض جغرافیایی", max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField("طول جغرافیایی", max_digits=9, decimal_places=6, null=True, blank=True)

    qr_caption = models.CharField(
        "متن زیر QR کد", max_length=80, blank=True, default="برای دیدن محصولات، اسکن کنید",
        help_text="همان متنی که روی کارت چاپی زیر QR نشان داده می‌شود.",
    )

    is_active = models.BooleanField("فعال", default=True, help_text="با غیرفعال کردن، صفحه فروشگاه از دسترس خارج می‌شود.")
    is_featured = models.BooleanField("بنر ویژه در صفحه اصلی", default=False)
    subscription_until = models.DateTimeField("اعتبار اشتراک تا", null=True, blank=True)
    subscription_started_at = models.DateTimeField("تاریخ فعال‌سازی اشتراک", null=True, blank=True)
    panel_token = models.CharField(max_length=64, unique=True, default=new_panel_token, editable=False)
    views = models.PositiveIntegerField("بازدید", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ShopQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "پت شاپ"
        verbose_name_plural = "پت شاپ‌ها"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        shrink_image(self.logo, 512)
        shrink_image(self.banner, 1600)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop", args=[self.slug])

    @property
    def public_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    @property
    def panel_link(self):
        return settings.SITE_URL + reverse("magic_login", args=[self.panel_token])

    @property
    def has_subscription(self):
        return bool(self.subscription_until and self.subscription_until > timezone.now())

    @property
    def is_public(self):
        return self.is_active and self.has_subscription

    @property
    def has_location(self):
        return self.lat is not None and self.lng is not None

    @property
    def days_left(self):
        if not self.has_subscription:
            return 0
        return max(0, (self.subscription_until - timezone.now()).days)

    def extend(self, days):
        start = self.subscription_until if self.has_subscription else timezone.now()
        self.subscription_started_at = start
        self.subscription_until = start + timedelta(days=days)
        self.save(update_fields=["subscription_started_at", "subscription_until"])

    def activate_for(self, days, start_at):
        self.subscription_started_at = start_at
        self.subscription_until = start_at + timedelta(days=days)
        self.save(update_fields=["subscription_started_at", "subscription_until"])

    def regenerate_token(self):
        self.panel_token = new_panel_token()
        self.save(update_fields=["panel_token"])


class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField("نام دسته", max_length=60)
    icon = models.CharField("آیکون", max_length=20, choices=PET_ICONS, default="paw")
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Product(models.Model):

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="دسته‌بندی"
    )
    name = models.CharField("نام محصول", max_length=120)
    brand = models.CharField("برند", max_length=60, blank=True)
    description = models.TextField("توضیحات", blank=True)
    image = models.ImageField("تصویر", upload_to="products/", blank=True)
    is_available = models.BooleanField("موجود است", default=True)
    is_featured = models.BooleanField("پیشنهاد ویژه", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        shrink_image(self.image, 1000)
        super().save(*args, **kwargs)


class Plan(models.Model):
    name = models.CharField("نام پلن", max_length=60)
    days = models.PositiveIntegerField("مدت (روز)")
    price = models.PositiveBigIntegerField("قیمت (ریال)")
    description = models.CharField("توضیح", max_length=200, blank=True)
    is_active = models.BooleanField("قابل خرید", default=True)
    is_popular = models.BooleanField("پیشنهاد ما", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["order", "days"]
        verbose_name = "پلن اشتراک"
        verbose_name_plural = "پلن‌های اشتراک"

    def __str__(self):
        return self.name

    @property
    def price_toman(self):
        return self.price // 10


class Payment(models.Model):
    PENDING, SUCCESS, FAILED = "pending", "success", "failed"
    STATUS_CHOICES = [(PENDING, "در انتظار"), (SUCCESS, "موفق"), (FAILED, "ناموفق")]
    GATEWAY_CHOICES = [("jibit", "جیبیت"), ("mock", "درگاه آزمایشی"), ("manual", "دستی (ادمین)")]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="payments", verbose_name="پت شاپ")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پلن")
    days = models.PositiveIntegerField("روز")
    amount = models.PositiveBigIntegerField("مبلغ (ریال)", default=0)
    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default=PENDING)
    gateway = models.CharField("درگاه", max_length=10, choices=GATEWAY_CHOICES, default="jibit")
    reference = models.CharField("شماره سفارش", max_length=40, unique=True, default=new_reference)
    purchase_id = models.CharField("شناسه خرید جیبیت", max_length=64, blank=True, db_index=True)
    psp_ref = models.CharField("کد پیگیری بانک", max_length=64, blank=True)
    card = models.CharField("کارت", max_length=32, blank=True)
    message = models.CharField("پیام", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return f"{self.shop} — {self.get_status_display()}"

    @property
    def amount_toman(self):
        return self.amount // 10


class JoinRequest(models.Model):
    shop_name = models.CharField("نام پت شاپ", max_length=100)
    owner_name = models.CharField("نام شما", max_length=100)
    phone = models.CharField("شماره تماس", max_length=20)
    city = models.CharField("شهر", max_length=50, blank=True)
    message = models.TextField("توضیحات", blank=True)
    handled = models.BooleanField("بررسی شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["handled", "-created_at"]
        verbose_name = "درخواست عضویت"
        verbose_name_plural = "درخواست‌های عضویت"

    def __str__(self):
        return self.shop_name

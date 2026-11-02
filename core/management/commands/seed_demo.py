import random
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from core.models import Category, Product, Shop

User = get_user_model()

DEMO = [
    ("پت هاوس", "pet-house", "همه‌چیز برای سگ و گربه", "تهران", "#0d9488", (13, 148, 136), (45, 212, 191)),
    ("دنیای پرندگان", "bird-world", "پرنده، قفس و دانه", "اصفهان", "#7c3aed", (124, 58, 237), (196, 181, 253)),
    ("آکواریوم آبی", "blue-aqua", "ماهی زینتی و تجهیزات آکواریوم", "شیراز", "#2563eb", (37, 99, 235), (147, 197, 253)),
    ("مهربان پت", "mehraban-pet", "غذا و لوازم بهداشتی حیوانات", "مشهد", "#ea580c", (234, 88, 12), (253, 186, 116)),
]

CATALOG = {
    "dog سگ": [("غذای خشک سگ بالغ", "رویال کنین"), ("استخوان تشویقی", "پت‌پرو"), ("قلاده چرمی", ""), ("شامپو سگ", "بایوگرومز")],
    "cat گربه": [("غذای خشک گربه", "رفلکس"), ("خاک گربه کلامپینگ", "کت‌لند"), ("اسکرچر چوبی", ""), ("کنسرو گربه", "جوسرا")],
    "fish ماهی": [("غذای پولکی ماهی", "تترا"), ("فیلتر آکواریوم", "سوبو"), ("گیاه مصنوعی", "")],
    "bird پرنده": [("دانه مخلوط قناری", "ورسله لاگا"), ("قفس فلزی متوسط", ""), ("ویتامین پرندگان", "")],
}


def png(size, c1, c2, shape="banner", seed=0):
    rnd = random.Random(seed)
    w, h = size
    img = Image.new("RGB", size, c1)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    for _ in range(14 if shape == "banner" else 5):
        r = rnd.randint(h // 10, h // 3)
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(min(255, v + 28) for v in c2))
    if shape != "banner":
        cx, cy, s = w // 2, h // 2 + h // 12, w // 6
        d.ellipse([cx - s, cy - s * 0.75, cx + s, cy + s * 0.75], fill="white")
        for dx, dy in ((-1.25, -1.2), (-0.45, -1.75), (0.45, -1.75), (1.25, -1.2)):
            x, y, r = cx + dx * s, cy + dy * s, s * 0.38
            d.ellipse([x - r, y - r, x + r, y + r], fill="white")
    buf = BytesIO()
    img.save(buf, "JPEG", quality=85)
    return ContentFile(buf.getvalue(), name="demo.jpg")


class Command(BaseCommand):
    help = "Creates demo pet shops with categories and products (password for all: demo1234)."

    def handle(self, *args, **opts):
        call_command("setup_site", stdout=self.stdout)
        for i, (name, slug, tagline, city, color, c1, c2) in enumerate(DEMO):
            if Shop.objects.filter(slug=slug).exists():
                self.stdout.write(f"= {slug}")
                continue
            owner = User.objects.create_user(username=slug, password="demo1234")
            shop = Shop(
                owner=owner, name=name, slug=slug, tagline=tagline, city=city, theme_color=color,
                description=f"{name} با بیش از ده سال سابقه در خدمت شما و حیوان خانگی‌تان.",
                phone="021-1234567" + str(i), address=f"{city}، خیابان اصلی، پلاک {10 + i}",
                working_hours="هر روز ۱۰ تا ۲۲", instagram=slug.replace("-", "_"), is_featured=i < 3,
            )
            shop.banner = png((1600, 520), c1, c2, "banner", seed=i)
            shop.logo = png((400, 400), c2, c1, "logo", seed=i + 10)
            shop.save()
            shop.extend(30)
            n = 0
            for order, (cat_name, items) in enumerate(CATALOG.items()):
                icon, label = cat_name.split(" ", 1)
                cat = Category.objects.create(shop=shop, name=label, icon=icon, order=order)
                for j, (pname, brand) in enumerate(items):
                    n += 1
                    Product.objects.create(
                        shop=shop, category=cat, name=pname, brand=brand,
                        description="محصول باکیفیت و اصل. برای اطلاع از موجودی و مشاوره با فروشگاه تماس بگیرید.",
                        image=png((800, 800), c2, c1, "product", seed=i * 100 + n),
                        is_available=(n % 5 != 0), is_featured=(n % 4 == 1), order=j,
                    )
            self.stdout.write(self.style.SUCCESS(f"+ {name} ({slug}) — {n} products"))
        self.stdout.write("Owner logins: <slug> / demo1234")

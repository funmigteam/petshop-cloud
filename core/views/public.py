from django.contrib import messages
from django.db.models import Count, F, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from ..branding import shop_qr_png
from ..forms import JoinRequestForm
from ..models import Category, Product, Shop, SiteConfig


def _can_manage(user, shop):
    return user.is_authenticated and (user.is_staff or shop.owner_id == user.id)


def home(request):
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    shops = Shop.objects.public().annotate(product_count=Count("products"))
    if q:
        shops = shops.filter(Q(name__icontains=q) | Q(tagline__icontains=q) | Q(products__name__icontains=q)).distinct()
    if city:
        shops = shops.filter(city=city)
    featured = Shop.objects.public().filter(is_featured=True).exclude(banner="")[:8]
    cities = (
        Shop.objects.public().exclude(city="").values_list("city", flat=True).distinct().order_by("city")
    )
    return render(request, "public/home.html", {
        "config": SiteConfig.get(),
        "shops": shops,
        "featured": featured if not (q or city) else [],
        "cities": cities,
        "q": q,
        "city": city,
    })


def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    manager = _can_manage(request.user, shop)
    if not shop.is_public and not manager:
        return render(request, "public/shop_closed.html", {"shop": shop}, status=403 if shop.is_active else 404)

    products = Product.objects.filter(shop=shop).select_related("category")
    categories = (
        Category.objects.filter(shop=shop)
        .prefetch_related(Prefetch("products", queryset=products))
        .annotate(n=Count("products"))
        .filter(n__gt=0)
    )
    uncategorized = [p for p in products if p.category_id is None]
    featured = [p for p in products if p.is_featured]
    if not manager:
        Shop.objects.filter(pk=shop.pk).update(views=F("views") + 1)
    return render(request, "public/shop.html", {
        "shop": shop,
        "categories": categories,
        "uncategorized": uncategorized,
        "featured": featured,
        "product_count": len(products),
        "is_manager": manager,
    })


@require_GET
def shop_qr(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    if request.GET.get("download") and not _can_manage(request.user, shop):
        return redirect("login")
    scale = 24 if request.GET.get("size") == "large" else 12
    resp = HttpResponse(shop_qr_png(shop, scale=scale), content_type="image/png")
    resp["Cache-Control"] = "public, max-age=86400"
    if request.GET.get("download"):
        resp["Content-Disposition"] = f'attachment; filename="qr-{shop.slug}.png"'
    return resp


def shop_qr_print(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    if not _can_manage(request.user, shop):
        return redirect("shop", slug=slug)
    return render(request, "public/qr_print.html", {"shop": shop})


def shops_map(request):
    return render(request, "public/map.html", {})


@require_GET
def shops_map_data(request):
    shops = Shop.objects.public().exclude(lat__isnull=True).exclude(lng__isnull=True)
    data = [
        {
            "id": s.pk,
            "name": s.name,
            "tagline": s.tagline,
            "city": s.city,
            "address": s.address,
            "lat": float(s.lat),
            "lng": float(s.lng),
            "url": s.get_absolute_url(),
            "logo": s.logo.url if s.logo else "",
            "theme_color": s.theme_color,
        }
        for s in shops
    ]
    return JsonResponse({"shops": data})


def join(request):
    form = JoinRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "درخواست شما ثبت شد. به‌زودی با شما تماس می‌گیریم.")
        return redirect("join")
    return render(request, "public/join.html", {"form": form, "config": SiteConfig.get()})

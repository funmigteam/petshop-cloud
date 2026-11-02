from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..utils import safe_next
from ..forms import CategoryForm, LocationForm, ProductForm, QrCaptionForm, SetPasswordForm, ShopSettingsForm
from ..models import Category, Product, Shop


def panel_view(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        shop = None
        if request.user.is_staff and request.session.get("acting_shop"):
            shop = Shop.objects.filter(pk=request.session["acting_shop"]).first()
        if shop is None:
            shop = getattr(request.user, "shop", None)
        if shop is None:
            if request.user.is_staff:
                messages.info(request, "برای ورود به پنل یک پت شاپ، از لیست فروشگاه‌ها «ورود به پنل» را بزنید.")
                return redirect("manage:shops")
            messages.error(request, "برای این حساب فروشگاهی ثبت نشده است.")
            return redirect("login")
        request.shop = shop
        return view(request, *args, **kwargs)

    return wrapper


def _ctx(request, section, **extra):
    return {"shop": request.shop, "section": section, "acting": request.user.is_staff, **extra}


@panel_view
def dashboard(request):
    shop = request.shop
    products = shop.products.all()
    return render(request, "panel/dashboard.html", _ctx(
        request, "dashboard",
        stats={
            "products": products.count(),
            "available": products.filter(is_available=True).count(),
            "categories": shop.categories.count(),
            "views": shop.views,
        },
        recent=products[:6],
        checklist=[
            ("لوگو را بارگذاری کنید", bool(shop.logo), "panel:settings"),
            ("بنر فروشگاه را اضافه کنید", bool(shop.banner), "panel:settings"),
            ("دسته‌بندی بسازید", shop.categories.exists(), "panel:categories"),
            ("اولین محصول را ثبت کنید", products.exists(), "panel:product_new"),
            ("شماره تماس و آدرس را وارد کنید", bool(shop.phone and shop.address), "panel:settings"),
        ],
    ))


@panel_view
def products(request):
    qs = request.shop.products.select_related("category")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q))
    if cat == "none":
        qs = qs.filter(category__isnull=True)
    elif cat.isdigit():
        qs = qs.filter(category_id=int(cat))
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    return render(request, "panel/products.html", _ctx(
        request, "products", page=page, q=q, cat=cat, categories=request.shop.categories.all(),
    ))


@panel_view
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk, shop=request.shop) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product, shop=request.shop)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.shop = request.shop
        obj.save()
        messages.success(request, "محصول ذخیره شد.")
        if "add_another" in request.POST:
            return redirect("panel:product_new")
        return redirect("panel:products")
    return render(request, "panel/product_form.html", _ctx(request, "products", form=form, product=product))


@panel_view
@require_POST
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk, shop=request.shop).delete()
    messages.success(request, "محصول حذف شد.")
    return redirect("panel:products")


@panel_view
@require_POST
def product_toggle(request, pk):
    p = get_object_or_404(Product, pk=pk, shop=request.shop)
    p.is_available = not p.is_available
    p.save(update_fields=["is_available"])
    return safe_next(request) or redirect("panel:products")


@panel_view
def categories(request, pk=None):
    editing = get_object_or_404(Category, pk=pk, shop=request.shop) if pk else None
    form = CategoryForm(request.POST or None, instance=editing)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.shop = request.shop
        obj.save()
        messages.success(request, "دسته‌بندی ذخیره شد.")
        return redirect("panel:categories")
    cats = request.shop.categories.annotate(n=Count("products"))
    return render(request, "panel/categories.html", _ctx(
        request, "categories", form=form, editing=editing, cats=cats,
    ))


@panel_view
@require_POST
def category_delete(request, pk):
    get_object_or_404(Category, pk=pk, shop=request.shop).delete()
    messages.success(request, "دسته‌بندی حذف شد. محصولات آن بدون دسته شدند.")
    return redirect("panel:categories")


@panel_view
def settings_view(request):
    form = ShopSettingsForm(request.POST or None, request.FILES or None, instance=request.shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "اطلاعات فروشگاه به‌روز شد.")
        return redirect("panel:settings")
    return render(request, "panel/settings.html", _ctx(request, "settings", form=form))


@panel_view
def location(request):
    form = LocationForm(request.POST or None, instance=request.shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "موقعیت مکانی فروشگاه روی نقشه ثبت شد.")
        return redirect("panel:location")
    return render(request, "panel/location.html", _ctx(request, "location", form=form))


@panel_view
def qr(request):
    form = QrCaptionForm(request.POST or None, instance=request.shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "متن زیر QR ذخیره شد.")
        return redirect("panel:qr")
    return render(request, "panel/qr.html", _ctx(request, "qr", form=form))


@panel_view
def password(request):
    form = SetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        owner = request.shop.owner
        owner.set_password(form.cleaned_data["password"])
        owner.save()
        if owner == request.user:
            update_session_auth_hash(request, owner)
        messages.success(request, "رمز عبور تغییر کرد.")
        return redirect("panel:dashboard")
    return render(request, "panel/password.html", _ctx(request, "password", form=form))


@panel_view
def exit_acting(request):
    request.session.pop("acting_shop", None)
    return redirect("manage:shop", pk=request.shop.pk)

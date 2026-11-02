from datetime import datetime, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..utils import safe_next
from ..forms import ExtendForm, LocationForm, SetPasswordForm, ShopAdminForm, ShopCreateForm, SiteConfigForm
from ..models import JoinRequest, Product, Shop, SiteConfig


def staff_view(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("panel:dashboard")
        return view(request, *args, **kwargs)

    return wrapper


def _ctx(section, **extra):
    return {"section": section, "pending_requests": JoinRequest.objects.filter(handled=False).count(), **extra}


@staff_view
def dashboard(request):
    now = timezone.now()
    shops = Shop.objects.all()
    return render(request, "manage/dashboard.html", _ctx(
        "dashboard",
        stats={
            "shops": shops.count(),
            "active": shops.filter(is_active=True, subscription_until__gt=now).count(),
            "expiring": shops.filter(subscription_until__gt=now, subscription_until__lt=now + timedelta(days=7)).count(),
            "products": Product.objects.count(),
        },
        expiring=shops.filter(subscription_until__gt=now, subscription_until__lt=now + timedelta(days=7))
        .order_by("subscription_until")[:8],
        recent_shops=shops.order_by("-created_at")[:6],
    ))


@staff_view
def shops(request):
    now = timezone.now()
    qs = Shop.objects.select_related("owner").annotate(product_count=Count("products"))
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(owner__username__icontains=q) | Q(phone__icontains=q))
    if status == "active":
        qs = qs.filter(is_active=True, subscription_until__gt=now)
    elif status == "expired":
        qs = qs.filter(Q(subscription_until__isnull=True) | Q(subscription_until__lte=now))
    elif status == "disabled":
        qs = qs.filter(is_active=False)
    page = Paginator(qs.order_by("-created_at"), 20).get_page(request.GET.get("page"))
    return render(request, "manage/shops.html", _ctx("shops", page=page, q=q, status=status))


@staff_view
def shop_create(request):
    form = ShopCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        shop = form.save()
        request.session["new_credentials"] = {
            "shop": shop.pk, "username": shop.owner.username, "password": form.generated_password,
        }
        messages.success(request, f"پت شاپ «{shop.name}» ساخته شد.")
        return redirect("manage:shop", pk=shop.pk)
    return render(request, "manage/shop_form.html", _ctx("shops", form=form, creating=True))


@staff_view
def shop_detail(request, pk):
    shop = get_object_or_404(Shop.objects.select_related("owner"), pk=pk)
    creds = request.session.get("new_credentials")
    if creds and creds.get("shop") == shop.pk:
        del request.session["new_credentials"]
    else:
        creds = None
    return render(request, "manage/shop_detail.html", _ctx(
        "shops",
        shop=shop,
        creds=creds,
        extend_form=ExtendForm(initial={"start_date": timezone.localdate()}),
        password_form=SetPasswordForm(),
        product_count=shop.products.count(),
    ))


@staff_view
def shop_edit(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    form = ShopAdminForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تغییرات ذخیره شد.")
        return redirect("manage:shop", pk=shop.pk)
    return render(request, "manage/shop_form.html", _ctx("shops", form=form, shop=shop, creating=False))


@staff_view
@require_POST
def shop_delete(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    if request.POST.get("confirm") != shop.slug:
        messages.error(request, "برای حذف، آدرس اختصاصی فروشگاه را دقیق وارد کنید.")
        return redirect("manage:shop", pk=pk)
    name = shop.name
    shop.owner.delete()
    messages.success(request, f"«{name}» حذف شد.")
    return redirect("manage:shops")


@staff_view
@require_POST
def shop_extend(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    form = ExtendForm(request.POST)
    if form.is_valid():
        days = form.cleaned_data["days"]
        start_date = form.cleaned_data["start_date"]
        start_at = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        shop.activate_for(days, start_at)
        messages.success(request, f"اشتراک از {start_date:%Y-%m-%d} به‌مدت {days} روز فعال شد.")
    else:
        messages.error(request, "تعداد روز نامعتبر است.")
    return redirect("manage:shop", pk=pk)


@staff_view
@require_POST
def shop_token(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    shop.regenerate_token()
    messages.success(request, "لینک پنل جدید ساخته شد. لینک قبلی دیگر کار نمی‌کند.")
    return redirect("manage:shop", pk=pk)


@staff_view
@require_POST
def shop_toggle(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    field = request.POST.get("field")
    if field in ("is_active", "is_featured"):
        setattr(shop, field, not getattr(shop, field))
        shop.save(update_fields=[field])
    return safe_next(request) or redirect("manage:shop", pk=pk)


@staff_view
@require_POST
def shop_password(request, pk):
    shop = get_object_or_404(Shop.objects.select_related("owner"), pk=pk)
    form = SetPasswordForm(request.POST)
    if form.is_valid():
        shop.owner.set_password(form.cleaned_data["password"])
        shop.owner.save()
        messages.success(request, "رمز عبور مالک تغییر کرد.")
    else:
        messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("manage:shop", pk=pk)


@staff_view
def shop_enter(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    request.session["acting_shop"] = shop.pk
    return redirect("panel:dashboard")


@staff_view
def shop_location(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    form = LocationForm(request.POST or None, instance=shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "موقعیت مکانی فروشگاه ذخیره شد.")
        return redirect("manage:shop", pk=pk)
    return render(request, "manage/shop_location.html", _ctx("shops", shop=shop, form=form))


@staff_view
def join_requests(request):
    return render(request, "manage/requests.html", _ctx("requests", items=JoinRequest.objects.all()[:200]))


@staff_view
@require_POST
def join_request_toggle(request, pk):
    item = get_object_or_404(JoinRequest, pk=pk)
    if request.POST.get("delete"):
        item.delete()
    else:
        item.handled = not item.handled
        item.save(update_fields=["handled"])
    return redirect("manage:requests")


@staff_view
def site_settings(request):
    form = SiteConfigForm(request.POST or None, instance=SiteConfig.get())
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تنظیمات سایت ذخیره شد.")
        return redirect("manage:site")
    return render(request, "manage/site.html", _ctx("site", form=form))

from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..utils import safe_next
from ..forms import ExtendForm, LocationForm, PlanForm, SetPasswordForm, ShopAdminForm, ShopCreateForm, SiteConfigForm
from ..models import JoinRequest, Payment, Plan, Product, Shop, SiteConfig


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
    paid = Payment.objects.filter(status=Payment.SUCCESS)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    six_months_ago = (month_start - timedelta(days=150)).replace(day=1)
    monthly = list(
        paid.filter(paid_at__gte=six_months_ago)
        .annotate(m=TruncMonth("paid_at")).values("m").annotate(total=Sum("amount")).order_by("m")
    )
    peak = max((row["total"] for row in monthly), default=0) or 1
    for row in monthly:
        row["pct"] = round(row["total"] * 100 / peak)

    return render(request, "manage/dashboard.html", _ctx(
        "dashboard",
        stats={
            "shops": shops.count(),
            "active": shops.filter(is_active=True, subscription_until__gt=now).count(),
            "expiring": shops.filter(subscription_until__gt=now, subscription_until__lt=now + timedelta(days=7)).count(),
            "products": Product.objects.count(),
            "revenue_month": paid.filter(paid_at__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0,
            "revenue_total": paid.aggregate(s=Sum("amount"))["s"] or 0,
        },
        monthly=monthly,
        recent_payments=Payment.objects.select_related("shop", "plan")[:8],
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
        extend_form=ExtendForm(),
        password_form=SetPasswordForm(),
        payments=shop.payments.select_related("plan")[:10],
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
        shop.extend(days)
        Payment.objects.create(
            shop=shop, days=days, amount=0, gateway="manual", status=Payment.SUCCESS,
            paid_at=timezone.now(), message=f"تمدید دستی توسط {request.user.username}",
        )
        messages.success(request, f"اشتراک {days} روز تغییر کرد.")
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
def plans(request, pk=None):
    editing = get_object_or_404(Plan, pk=pk) if pk else None
    form = PlanForm(request.POST or None, instance=editing)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "پلن ذخیره شد.")
        return redirect("manage:plans")
    return render(request, "manage/plans.html", _ctx(
        "plans", form=form, editing=editing,
        plans=Plan.objects.annotate(sold=Count("payment", filter=Q(payment__status=Payment.SUCCESS))),
    ))


@staff_view
@require_POST
def plan_delete(request, pk):
    get_object_or_404(Plan, pk=pk).delete()
    messages.success(request, "پلن حذف شد.")
    return redirect("manage:plans")


@staff_view
def payments(request):
    qs = Payment.objects.select_related("shop", "plan")
    status = request.GET.get("status", "")
    if status in dict(Payment.STATUS_CHOICES):
        qs = qs.filter(status=status)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(shop__name__icontains=q) | Q(purchase_id__icontains=q) | Q(reference__icontains=q))
    total = qs.filter(status=Payment.SUCCESS).aggregate(s=Sum("amount"))["s"] or 0
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "manage/payments.html", _ctx(
        "payments", page=page, status=status, q=q, total=total, statuses=Payment.STATUS_CHOICES,
    ))


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

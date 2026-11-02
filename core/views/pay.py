import logging

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from ..jibit import JibitError, get_client
from ..models import Payment

log = logging.getLogger(__name__)


def start_payment(request, payment):
    client = get_client()
    payment.gateway = "mock" if settings.JIBIT_MOCK else "jibit"
    callback = settings.SITE_URL + reverse("pay_callback")
    try:
        purchase_id, url = client.create_purchase(
            amount=payment.amount,
            reference=payment.reference,
            callback_url=callback,
            user_identifier=payment.shop.slug,
            description=f"اشتراک {payment.plan.name if payment.plan else ''} — {payment.shop.name}",
        )
    except JibitError as exc:
        payment.status, payment.message = Payment.FAILED, str(exc)[:255]
        payment.save()
        return redirect("pay_result", ref=payment.reference)
    payment.purchase_id = purchase_id
    payment.save()
    return redirect(url)


@csrf_exempt
def callback(request):
    data = request.POST if request.method == "POST" else request.GET
    purchase_id = data.get("purchaseId", "")
    status = data.get("status", "")
    if not purchase_id:
        raise Http404
    payment = get_object_or_404(Payment, purchase_id=purchase_id)
    finalize(payment, status, data.get("amount"))
    return redirect("pay_result", ref=payment.reference)


def finalize(payment, callback_status, callback_amount=None):
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("shop").get(pk=payment.pk)
        if payment.status != Payment.PENDING:
            return payment
        if callback_status != "SUCCESSFUL":
            payment.status, payment.message = Payment.FAILED, "پرداخت توسط کاربر لغو شد یا ناموفق بود."
            payment.save()
            return payment
        if callback_amount not in (None, "") and str(callback_amount) != str(payment.amount):
            payment.status, payment.message = Payment.FAILED, "مبلغ برگشتی با سفارش مطابقت ندارد."
            payment.save()
            return payment
        client = get_client()
        try:
            ok = client.verify(payment.purchase_id)
        except JibitError as exc:
            payment.message = f"خطا در تأیید: {exc}"[:255]
            payment.save()
            return payment
        if not ok:
            payment.status, payment.message = Payment.FAILED, "تراکنش توسط درگاه تأیید نشد."
            payment.save()
            return payment
        try:
            info = client.inquiry(payment.purchase_id)
            payment.card = info.get("pspMaskedCardNumber", "")[:32]
            payment.psp_ref = str(info.get("pspReferenceNumber") or info.get("pspRrn") or "")[:64]
        except JibitError:
            pass
        payment.status, payment.paid_at, payment.message = Payment.SUCCESS, timezone.now(), "پرداخت موفق"
        payment.save()
        payment.shop.extend(payment.days)
    return payment


def result(request, ref):
    payment = get_object_or_404(Payment.objects.select_related("shop", "plan"), reference=ref)
    return render(request, "pay/result.html", {"payment": payment, "shop": payment.shop})


def mock_gateway(request, ref):
    if not settings.JIBIT_MOCK:
        raise Http404
    payment = get_object_or_404(Payment, reference=ref, status=Payment.PENDING)
    if request.method == "POST":
        status = "SUCCESSFUL" if request.POST.get("action") == "pay" else "FAILED"
        get_client().mark(payment.purchase_id, status)
        return render(request, "pay/mock_redirect.html", {
            "action": reverse("pay_callback"),
            "fields": {"purchaseId": payment.purchase_id, "amount": payment.amount, "status": status},
        })
    return render(request, "pay/mock.html", {"payment": payment})

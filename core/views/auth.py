from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ..forms import LoginForm
from ..models import Shop


def _home_for(user):
    return "manage:dashboard" if user.is_staff else "panel:dashboard"


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_home_for(request.user))
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        nxt = request.GET.get("next")
        if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
            return redirect(nxt)
        return redirect(_home_for(form.get_user()))
    return render(request, "auth/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


def magic_login(request, token):
    shop = get_object_or_404(Shop.objects.select_related("owner"), panel_token=token)
    if not shop.owner.is_active:
        messages.error(request, "حساب این فروشگاه غیرفعال است.")
        return redirect("login")
    if request.user.is_authenticated and request.user.is_staff:
        request.session["acting_shop"] = shop.pk
        return redirect("panel:dashboard")
    login(request, shop.owner, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("panel:dashboard")

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request, field="next"):
    nxt = request.POST.get(field) or request.GET.get(field)
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return None

import logging

import requests
from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

TOKEN_CACHE_KEY = "jibit:access-token"
TOKEN_TTL = 60 * 60 * 6
MOCK_CACHE_PREFIX = "jibit:mock:"


class JibitError(Exception):
    pass


class JibitClient:
    def __init__(self):
        self.base = settings.JIBIT_BASE_URL
        self.timeout = settings.JIBIT_TIMEOUT

    def _request(self, method, path, json=None, auth=True):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth:
            headers["Authorization"] = "Bearer " + self._token()
        try:
            resp = requests.request(method, self.base + path, json=json, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise JibitError(f"ارتباط با درگاه برقرار نشد: {exc}") from exc
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code == 401 and auth:
            cache.delete(TOKEN_CACHE_KEY)
        if resp.status_code >= 400:
            errors = data.get("errors") or []
            msg = "، ".join(e.get("message") or e.get("code", "") for e in errors) or f"HTTP {resp.status_code}"
            log.warning("Jibit %s %s failed: %s", method, path, data)
            raise JibitError(msg)
        return data

    def _token(self):
        token = cache.get(TOKEN_CACHE_KEY)
        if token:
            return token
        data = self._request(
            "POST", "/tokens",
            json={"apiKey": settings.JIBIT_API_KEY, "secretKey": settings.JIBIT_SECRET_KEY},
            auth=False,
        )
        token = data.get("accessToken")
        if not token:
            raise JibitError("توکن جیبیت دریافت نشد.")
        cache.set(TOKEN_CACHE_KEY, token, TOKEN_TTL)
        return token

    def create_purchase(self, amount, reference, callback_url, user_identifier="", description=""):
        payload = {
            "amount": int(amount),
            "currency": "IRR",
            "callbackUrl": callback_url,
            "clientReferenceNumber": reference,
            "userIdentifier": user_identifier or reference,
            "description": description[:200],
        }
        data = self._request("POST", "/purchases", json=payload)
        purchase_id, url = data.get("purchaseId"), data.get("pspSwitchingUrl")
        if not purchase_id or not url:
            raise JibitError("پاسخ نامعتبر از درگاه.")
        return str(purchase_id), url

    def verify(self, purchase_id):
        data = self._request("GET", f"/purchases/{purchase_id}/verify")
        return data.get("status") in ("SUCCESSFUL", "ALREADY_VERIFIED")

    def inquiry(self, purchase_id):
        data = self._request("GET", f"/purchases?purchaseId={purchase_id}")
        elements = data.get("elements") or []
        return elements[0] if elements else {}


class MockJibitClient:

    def create_purchase(self, amount, reference, callback_url, user_identifier="", description=""):
        from django.urls import reverse

        purchase_id = "MOCK-" + reference[:12]
        cache.set(MOCK_CACHE_PREFIX + purchase_id, "PENDING", 3600)
        return purchase_id, reverse("pay_mock", args=[reference])

    def mark(self, purchase_id, status):
        cache.set(MOCK_CACHE_PREFIX + purchase_id, status, 3600)

    def verify(self, purchase_id):
        return cache.get(MOCK_CACHE_PREFIX + purchase_id) == "SUCCESSFUL"

    def inquiry(self, purchase_id):
        return {"pspMaskedCardNumber": "6037-99**-****-1234", "pspReferenceNumber": "MOCK" + purchase_id[-6:]}


def get_client():
    return MockJibitClient() if settings.JIBIT_MOCK else JibitClient()

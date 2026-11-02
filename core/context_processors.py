from django.conf import settings
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from .models import SiteConfig
from .templatetags.fa import gregorian_to_jalali


def site(request):
    today = timezone.localdate()
    return {
        "site_config": SimpleLazyObject(SiteConfig.get),
        "JALALI_YEAR": gregorian_to_jalali(today.year, today.month, today.day)[0],
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "JIBIT_MOCK": settings.JIBIT_MOCK,
        "MAP_TILE_URL": settings.MAP_TILE_URL,
        "MAP_TILE_ATTRIBUTION": settings.MAP_TILE_ATTRIBUTION,
        "MAP_DEFAULT_LAT": settings.MAP_DEFAULT_LAT,
        "MAP_DEFAULT_LNG": settings.MAP_DEFAULT_LNG,
    }

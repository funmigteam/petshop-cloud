from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "pet-online.ir — Django admin"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
]

if settings.SERVE_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
    if not settings.DEBUG:
        urlpatterns += [
            re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
        ]

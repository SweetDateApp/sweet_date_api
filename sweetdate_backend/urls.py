from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",   include("api.urls")),
]

if settings.SERVE_MEDIA:
    media_prefix = settings.MEDIA_URL.strip("/")
    urlpatterns += [
        re_path(rf"^{media_prefix}/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

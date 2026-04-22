from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core
    path('', include('core.urls')),

    # Docs
    path('', include('docs.urls')),

    # AI physics module
    path('ai/', include('ai_module.urls')),

    # Serve user-uploaded media (documents + thumbnails) in both DEBUG and
    # production. django.conf.urls.static.static() is a no-op when DEBUG=False,
    # so we wire the serve view directly.
    re_path(
        r'^media/(?P<path>.*)$',
        static_serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]

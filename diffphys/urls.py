from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core
    path('', include('core.urls')),

    # Docs
    path('', include('docs.urls')),

    # 🔥 AI PHYSICS MODULE (ENG MUHIM)
    path('ai/', include('ai_module.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

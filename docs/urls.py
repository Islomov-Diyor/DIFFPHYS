from django.urls import path
from . import views

urlpatterns = [
    # Taqdimotlar
    path('presentations/', views.presentations_view, name='presentations'),

    # ✅ ALIAS: eski template'lar presentation_list deb chaqirsa ham ishlasin
    path('presentations/', views.presentations_view, name='presentation_list'),

    # Qolganlari
    path('practicals/', views.practicals_view, name='practicals'),
    path('videodarslar/', views.video_lessons, name='videos'),
    path('nazorat/', views.nazorat_view, name='nazorat'),
]

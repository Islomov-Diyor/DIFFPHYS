from django.urls import path
from . import views

urlpatterns = [
    # Presentations
    path("presentations/", views.presentations_view, name="presentations"),
    path("presentations/<int:pk>/download/", views.download_presentation, name="download_presentation"),
    path("presentations/<int:pk>/thumb.png", views.presentation_thumb, name="presentation_thumb"),


    # Practicals
    path("practicals/", views.practicals_view, name="practicals"),
    path("practicals/<int:pk>/download/", views.download_practical, name="download_practical"),
    # ✅ Practical thumbnail
    path("practicals/<int:pk>/thumb.png", views.practical_thumb, name="practical_thumb"),

    # Videos
    path("videodarslar/", views.video_lessons, name="videos"),

    # Nazorat
    path("nazorat/", views.nazorat_view, name="nazorat"),
]
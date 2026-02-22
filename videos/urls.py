from django.urls import path
from . import views

urlpatterns = [
    path("videos/", views.index, name="videos_index"),
]

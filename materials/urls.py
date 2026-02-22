from django.urls import path
from . import views

urlpatterns = [
    path("materials/", views.index, name="materials_index"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("testsystem/", views.index, name="testsystem_index"),
]

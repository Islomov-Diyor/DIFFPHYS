# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("maruzalar/", views.lecture_list, name="lecture_list"),
    path("maruzalar/<int:pk>/download/", views.download_document, name="download_document"),
    path("maruzalar/<int:pk>/test/", views.lecture_test, name="lecture_test"),

    path("contact/", views.contact_view, name="contact"),
    path("student/", views.is_stu, name="is_stu"),
    path("teacher/", views.is_tech, name="is_tech"),

    path("metodik/", views.metodik_taminot, name="metodik_taminot"),
    path("metodik/ped/<int:pk>/download/", views.download_ped_texnologiya, name="download_ped_texnologiya"),
    path("metodik/mez/<int:pk>/download/", views.download_baholash_mezon, name="download_baholash_mezon"),
    path("metodik/maslahat/<int:pk>/download/", views.download_maslahat, name="download_maslahat"),
    path("metodik/mashgulot/<int:pk>/download/", views.download_mashgulot, name="download_mashgulot"),

    path("meyoriy/", views.meyoriy_hujjatlar, name="meyoriy_hujjatlar"),
    path("meyoriy/<int:pk>/download/", views.download_hujjat, name="download_hujjat"),

    path("nazorat/", views.nazorat_view, name="nazorat_view"),
]

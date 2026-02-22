# ai_module/urls.py
from django.urls import path
from . import views_physics

app_name = "ai_module"

urlpatterns = [
    # Prujina–massa (eski)
    path("prujina-massa/", views_physics.prujina_massa_view, name="prujina_massa"),
    path("mass-spring/", views_physics.prujina_massa_view, name="mass_spring"),
    path("prujina-massa/pdf/", views_physics.mass_spring_pdf_view, name="prujina_massa_pdf"),
    path("mass-spring/pdf/", views_physics.mass_spring_pdf_view, name="mass_spring_pdf"),

    # RLC
    path("rlc/", views_physics.rlc_series_view, name="rlc_series"),
    path("rlc/pdf/", views_physics.rlc_pdf_view, name="rlc_pdf"),

    # Erkin tushish + qarshilik
    path("free-fall/", views_physics.free_fall_view, name="free_fall"),
    path("free-fall/pdf/", views_physics.free_fall_pdf_view, name="free_fall_pdf"),

    # Radioaktiv parchalanish
    path("decay/", views_physics.decay_view, name="decay"),
    path("decay/pdf/", views_physics.decay_pdf_view, name="decay_pdf"),

    # Fourier issiqlik tenglamasi
    path("heat-fourier/", views_physics.heat_fourier_view, name="heat_fourier"),
    path("heat-fourier/pdf/", views_physics.heat_fourier_pdf_view, name="heat_fourier_pdf"),

    # mass-spring2
    path("mass-spring2/", views_physics.mass_spring2_view, name="mass_spring2"),
    path("mass-spring2/pdf/", views_physics.mass_spring2_pdf, name="mass_spring2_pdf"),

    # ✅ RC
    path("rc/", views_physics.rc_circuit_view, name="rc_circuit"),
    path("rc/pdf/", views_physics.rc_circuit_pdf_view, name="rc_circuit_pdf"),

    # ✅ RL
    path("rl/", views_physics.rl_circuit_view, name="rl_circuit"),
    path("rl/pdf/", views_physics.rl_circuit_pdf_view, name="rl_circuit_pdf"),
]

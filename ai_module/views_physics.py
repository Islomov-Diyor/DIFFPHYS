# ai_module/views_physics.py

import json  # ✅ SHART: plotly_payload = json.dumps(...) uchun
import base64
import io
import math
from io import BytesIO

import numpy as np

import matplotlib
matplotlib.use("Agg")  # serverda grafik chizish uchun
import matplotlib.pyplot as plt

import plotly.graph_objects as go
from plotly.offline import plot

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template

try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

from .forms import (
    MassSpringForm,
    RLCSeriesForm,
    FreeFallDragForm,
    RadioactiveDecayForm,
)

# SciPy (bo'lsa ishlatamiz, bo'lmasa RK4 fallback)
try:
    from scipy.integrate import solve_ivp
    SCIPY_OK = True
except Exception:
    solve_ivp = None
    SCIPY_OK = False

# =========================
#  UMUMIY YORDAMCHI FUNKSIYALAR
# =========================
def _safe_center_range(
    value: float,
    default_min: float = 0.0,
    default_max: float = 1.0,
    factor_min: float = 0.5,
    factor_max: float = 1.5,
):
    """
    Grafik/slider uchun xavfsiz [min,max] oraliq.
    value atrofida factor_min..factor_max ko‘paytirib range beradi.
    value yaroqsiz bo‘lsa default_min/default_max qaytaradi.

    Misol:
      k_min,k_max = _safe_center_range(k, 10,200, 0.25,2.0)
    """
    try:
        v = float(value)
        if not np.isfinite(v):
            return float(default_min), float(default_max)

        lo = v * float(factor_min)
        hi = v * float(factor_max)

        # agar value manfiy bo‘lsa yoki lo/hi teskari bo‘lsa to‘g‘rilaymiz
        lo, hi = (min(lo, hi), max(lo, hi))

        # 0 ga juda yaqin bo‘lsa default’dan foydalanamiz
        if abs(hi - lo) < 1e-12:
            return float(default_min), float(default_max)

        # default bilan kesish (juda tor/keraksiz bo‘lib qolmasin)
        lo = min(lo, float(default_min)) if lo > float(default_min) else lo
        hi = max(hi, float(default_max)) if hi < float(default_max) else hi

        # yana teskari bo‘lib qolsa
        lo, hi = (min(lo, hi), max(lo, hi))
        return float(lo), float(hi)

    except Exception:
        return float(default_min), float(default_max)

def _plot_to_base64(fig) -> str:
    """
    Matplotlib figure -> base64 PNG string
    Template ichida:
      <img src="data:image/png;base64,{{ plot_x }}">
    """
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=140)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ✅ ba'zi joylarda _fig_to_base64 deb chaqirilgan bo‘lishi mumkin
_fig_to_base64 = _plot_to_base64


def _render_to_pdf(template_src: str, context: dict) -> bytes:
    """
    HTML template -> PDF bytes (xhtml2pdf)
    """
    template = get_template(template_src)
    html = template.render(context)
    result = io.BytesIO()
    pisa.CreatePDF(html, dest=result, encoding="utf-8")
    return result.getvalue()


def _pdf_download_response(pdf_bytes: bytes, filename: str = "report.pdf") -> HttpResponse:
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp["X-Content-Type-Options"] = "nosniff"
    return resp


# =========================
#  PRUJINA–MASSA (Mass–Spring–Damper)
# =========================
def _solve_mass_spring(m: float, k: float, c: float, x0: float, v0: float, t_end: float, dt: float):
    """
    ODE:
        x' = v
        v' = -(c/m) v - (k/m) x
    """
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    def f(ti, y):
        x, v = y
        dx = v
        dv = -(c / m) * v - (k / m) * x
        return [dx, dv]

    if SCIPY_OK:
        sol = solve_ivp(
            f,
            t_span=(0.0, t_end),
            y0=[x0, v0],
            t_eval=t,
            method="RK45",
            rtol=1e-6,
            atol=1e-9,
        )
        x = sol.y[0]
        v = sol.y[1]
    else:
        # RK4 fallback
        y = np.zeros((len(t), 2), dtype=float)
        y[0] = [x0, v0]

        for i in range(len(t) - 1):
            h = dt
            ti = t[i]
            yi = y[i]

            k1 = np.array(f(ti, yi))
            k2 = np.array(f(ti + h / 2, yi + h * k1 / 2))
            k3 = np.array(f(ti + h / 2, yi + h * k2 / 2))
            k4 = np.array(f(ti + h, yi + h * k3))

            y[i + 1] = yi + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

        x = y[:, 0]
        v = y[:, 1]

    # Energiya: E = 1/2 m v^2 + 1/2 k x^2
    E = 0.5 * m * (v**2) + 0.5 * k * (x**2)

    return t, x, v, E


def _build_conclusion_mass_spring(m: float, k: float, c: float, x: np.ndarray, v: np.ndarray, E: np.ndarray) -> str:
    omega0 = math.sqrt(k / m)  # rad/s
    f0 = omega0 / (2.0 * math.pi)
    c_crit = 2.0 * math.sqrt(k * m)
    zeta = 0.0 if c_crit == 0 else c / c_crit

    omega_d = None
    T_d = None
    if 0.0 < zeta < 1.0:
        omega_d = omega0 * math.sqrt(1.0 - zeta**2)
        if omega_d > 0:
            T_d = 2.0 * math.pi / omega_d

    x_abs_max = float(np.max(np.abs(x)))
    v_abs_max = float(np.max(np.abs(v)))
    E0 = float(E[0])
    E_end = float(E[-1])

    drop_pct = 0.0
    if abs(E0) > 1e-12:
        drop_pct = max(0.0, (E0 - E_end) / abs(E0) * 100.0)

    eps = 1e-12
    if c <= eps or zeta <= eps:
        regime = "so‘nishsiz (ideal garmonik tebranish)"
        base = (
            "Xulosa: Model natijalari prujina–massa tizimida ideal garmonik tebranish yuz berishini ko‘rsatdi. "
            "x(t) va v(t) grafiklari sinusoidal xarakterga ega bo‘lib, E(t) deyarli o‘zgarmas bo‘ldi."
        )
    elif abs(zeta - 1.0) < 1e-3:
        regime = "kritik so‘nish"
        base = (
            "Xulosa: Tizim kritik so‘nish chegarasiga yaqin holatda bo‘lib, muvozanatga eng tez tebranishsiz "
            "yaqinlashish kuzatildi."
        )
    elif zeta < 1.0:
        regime = "so‘nuvchi tebranish (underdamped)"
        base = (
            "Xulosa: Sonli modellashtirish natijalariga ko‘ra tizimda so‘nuvchi tebranish kuzatildi. "
            "Amplituda vaqt o‘tishi bilan kamaydi va E(t) pasaydi."
        )
    else:
        regime = "aperiodik (tebranishsiz) so‘nish (overdamped)"
        base = (
            "Xulosa: Qarshilik koeffitsienti katta bo‘lgani sababli tizim tebranishsiz (aperiodik) holatda "
            "muvozanatga silliq yaqinlashdi."
        )

    details = (
        f" Rejim: {regime}. "
        f"Tabiiy chastota: ω0≈{omega0:.3f} rad/s (f0≈{f0:.3f} Hz), ζ≈{zeta:.3f}."
    )
    if omega_d is not None and T_d is not None:
        details += f" So‘nuvchi chastota: ωd≈{omega_d:.3f} rad/s, period: T≈{T_d:.3f} s."
    details += f" | |x|max≈{x_abs_max:.4f} m, |v|max≈{v_abs_max:.4f} m/s"
    if c > eps:
        details += f", Energiya kamayishi≈{drop_pct:.1f}%"

    return base + details


def _build_mass_spring_surface_div(m, k_center, c, x0, v0, t_end, dt, k_min, k_max, k_steps, z_mode):
    """
    3D Surface (Prujina–massa):
      X = t
      Y = k (qattiqlik koeff.)
      Z = x(t) yoki v(t)

    z_mode: "X" yoki "V"
    """
    k_steps = int(max(10, k_steps))
    k_vals = np.linspace(float(k_min), float(k_max), k_steps, dtype=float)
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    Z = np.zeros((len(k_vals), len(t)), dtype=float)

    for i, k in enumerate(k_vals):
        tt, x, v, _E = _solve_mass_spring(float(m), float(k), float(c), float(x0), float(v0), float(t_end), float(dt))
        # tt va t uzunligi bir xil bo‘lishi kerak (dt bilan)
        Z[i, :] = v if z_mode == "V" else x

    z_title = "v(t) (m/s)" if z_mode == "V" else "x(t) (m)"

    fig = go.Figure(data=[go.Surface(x=t, y=k_vals, z=Z)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="k (N/m)",
            zaxis_title=z_title,
        ),
    )
    return plot(fig, output_type="div", include_plotlyjs=True)


def prujina_massa_view(request):
    img_x = img_v = img_E = None
    stats = None
    conclusion = None
    surface_div = None  # <-- YANGI (UI 3D)

    if request.method == "POST":
        form = MassSpringForm(request.POST)
        if form.is_valid():
            m = float(form.cleaned_data["m"])
            k = float(form.cleaned_data["k"])
            c = float(form.cleaned_data.get("c") or 0.0)
            x0 = float(form.cleaned_data["x0"])
            v0 = float(form.cleaned_data["v0"])
            t_end = float(form.cleaned_data["t_end"])
            dt = float(form.cleaned_data["dt"])

            t, x, v, E = _solve_mass_spring(m, k, c, x0, v0, t_end, dt)

            fig1 = plt.figure()
            plt.plot(t, x)
            plt.xlabel("t (s)")
            plt.ylabel("x (m)")
            plt.title("Prujina–massa: siljish x(t)")
            img_x = _plot_to_base64(fig1)

            fig2 = plt.figure()
            plt.plot(t, v)
            plt.xlabel("t (s)")
            plt.ylabel("v (m/s)")
            plt.title("Tezlik v(t)")
            img_v = _plot_to_base64(fig2)

            fig3 = plt.figure()
            plt.plot(t, E)
            plt.xlabel("t (s)")
            plt.ylabel("E (J)")
            plt.title("Umumiy energiya E(t)")
            img_E = _plot_to_base64(fig3)

            stats = {
                "x_min": float(np.min(x)),
                "x_max": float(np.max(x)),
                "v_min": float(np.min(v)),
                "v_max": float(np.max(v)),
            }

            conclusion = _build_conclusion_mass_spring(m, k, c, x, v, E)

            # ---------- 3D Surface (faqat UI) ----------
            k_min, k_max = _safe_center_range(k, default_min=10.0, default_max=200.0, factor_min=0.25, factor_max=2.0)
            k_steps = int(request.POST.get("k_steps", 25))
            z_mode = (request.POST.get("z_mode", "X") or "X").strip().upper()
            if z_mode not in ("X", "V"):
                z_mode = "X"

            surface_div = _build_mass_spring_surface_div(
                m=m, k_center=k, c=c, x0=x0, v0=v0, t_end=t_end, dt=dt,
                k_min=k_min, k_max=k_max, k_steps=k_steps, z_mode=z_mode
            )

    else:
        form = MassSpringForm()

    return render(request, "ai_module/mass_spring.html", {
        "form": form,
        "img_x": img_x,
        "img_v": img_v,
        "img_E": img_E,
        "stats": stats,
        "conclusion": conclusion,
        "surface_div": surface_div,  # <-- YANGI
        "scipy_ok": SCIPY_OK,
    })


def mass_spring_pdf_view(request):
    def _p(key, default):
        v = request.GET.get(key) or request.POST.get(key)
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return default

    m = _p("m", 1.0)
    k = _p("k", 10.0)
    c = _p("c", 0.5)
    x0 = _p("x0", 1.0)
    v0 = _p("v0", 0.0)
    t_end = _p("t_end", 10.0)
    dt = _p("dt", 0.01)

    t, x, v, E = _solve_mass_spring(m, k, c, x0, v0, t_end, dt)
    conclusion = _build_conclusion_mass_spring(m, k, c, x, v, E)

    imgs = []
    for (title, ydata, ylabel) in [
        ("Siljish x(t)", x, "x (m)"),
        ("Tezlik v(t)", v, "v (m/s)"),
        ("Energiya E(t)", E, "E (J)"),
    ]:
        fig = plt.figure()
        plt.plot(t, ydata)
        plt.xlabel("t (s)")
        plt.ylabel(ylabel)
        plt.title(title)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)
    _pdf_header(cpdf, "Prujina–massa — PDF hisobot")
    _pdf_params_block(cpdf, [
        ("m (kg)", f"{m:g}"), ("k (N/m)", f"{k:g}"), ("c (N·s/m)", f"{c:g}"),
        ("x0 (m)", f"{x0:g}"), ("v0 (m/s)", f"{v0:g}"),
        ("T (s)", f"{t_end:g}"), ("dt (s)", f"{dt:g}"),
    ], y=27.2*cm)

    x0_pdf, w, h, y_top = 2*cm, 17.0*cm, 5.8*cm, 22.0*cm
    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h + 0.5*cm)
        cpdf.drawImage(ImageReader(img_buf), x0_pdf, y - h, width=w, height=h, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, conclusion)
    _pdf_page_number(cpdf, 1)
    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="MassSpring_natijalar.pdf"'
    return resp


# =========================
#  RLC SERIES (ketma-ket R–L–C)
# =========================
def _solve_rlc_series(R: float, L: float, C: float, V0: float, q0: float, i0: float, t_end: float, dt: float):
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    def f(ti, y):
        q, i = y
        dq = i
        di = (V0 - R * i - (q / C)) / L
        return [dq, di]

    if SCIPY_OK:
        sol = solve_ivp(
            f,
            t_span=(0.0, t_end),
            y0=[q0, i0],
            t_eval=t,
            method="RK45",
            rtol=1e-6,
            atol=1e-9,
        )
        q = sol.y[0]
        i = sol.y[1]
    else:
        y = np.zeros((len(t), 2), dtype=float)
        y[0] = [q0, i0]
        for idx in range(len(t) - 1):
            h = dt
            ti = t[idx]
            yi = y[idx]

            k1 = np.array(f(ti, yi))
            k2 = np.array(f(ti + h / 2, yi + h * k1 / 2))
            k3 = np.array(f(ti + h / 2, yi + h * k2 / 2))
            k4 = np.array(f(ti + h, yi + h * k3))

            y[idx + 1] = yi + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

        q = y[:, 0]
        i = y[:, 1]

    Vc = q / C
    return t, q, i, Vc


def _build_conclusion_rlc(R: float, L: float, C: float, V0: float, q: np.ndarray, i: np.ndarray, Vc: np.ndarray) -> str:
    omega0 = 1.0 / math.sqrt(L * C)
    f0 = omega0 / (2.0 * math.pi)
    zeta = (R / 2.0) * math.sqrt(C / L)

    omega_d = None
    T_d = None
    if 0.0 < zeta < 1.0:
        omega_d = omega0 * math.sqrt(1.0 - zeta**2)
        if omega_d > 0:
            T_d = 2.0 * math.pi / omega_d

    i_abs_max = float(np.max(np.abs(i)))
    vc_abs_max = float(np.max(np.abs(Vc)))

    eps = 1e-12
    if R <= eps or zeta <= eps:
        regime = "so‘nishsiz (ideal tebranish)"
        base = "Xulosa: RLC zanjirida ideal tebranish rejimi kuzatildi."
    elif abs(zeta - 1.0) < 1e-3:
        regime = "kritik so‘nish"
        base = "Xulosa: Zanjir kritik so‘nish rejimiga yaqin holatda barqarorlashdi."
    elif zeta < 1.0:
        regime = "so‘nuvchi tebranish (underdamped)"
        base = "Xulosa: Zanjirda so‘nuvchi tebranish kuzatildi, amplituda vaqt o‘tishi bilan kamaydi."
    else:
        regime = "aperiodik (tebranishsiz) so‘nish (overdamped)"
        base = "Xulosa: Qarshilik katta bo‘lgani sababli tebranishlar yuz bermadi (aperiodik rejim)."

    details = (
        f" Rejim: {regime}. "
        f"ω0≈{omega0:.3f} rad/s (f0≈{f0:.3f} Hz), ζ≈{zeta:.3f}."
    )
    if omega_d is not None and T_d is not None:
        details += f" ωd≈{omega_d:.3f} rad/s, T≈{T_d:.3f} s."
    details += f" | |i|max≈{i_abs_max:.4f} A, |Vc|max≈{vc_abs_max:.4f} V (V0={V0} V)."

    return base + details


def _build_rlc_surface_div(R_center, L, C, V0, q0, i0, t_end, dt, R_min, R_max, R_steps, z_mode):
    """
    3D Surface (RLC):
      X = t
      Y = R (Ohm)
      Z = i(t) yoki Vc(t)

    z_mode: "I" yoki "VC"
    """
    R_steps = int(max(10, R_steps))
    R_vals = np.linspace(float(R_min), float(R_max), R_steps, dtype=float)
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    Z = np.zeros((len(R_vals), len(t)), dtype=float)
    for i, R in enumerate(R_vals):
        tt, q, cur, vc = _solve_rlc_series(float(R), float(L), float(C), float(V0), float(q0), float(i0), float(t_end), float(dt))
        Z[i, :] = vc if z_mode == "VC" else cur

    z_title = "Vc(t) (V)" if z_mode == "VC" else "i(t) (A)"

    fig = go.Figure(data=[go.Surface(x=t, y=R_vals, z=Z)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="R (Ω)",
            zaxis_title=z_title,
        ),
    )
    return plot(fig, output_type="div", include_plotlyjs=True)


def rlc_series_view(request):
    img_q = img_i = img_vc = None
    stats = None
    conclusion = None
    surface_div = None  # <-- YANGI (UI 3D)

    if request.method == "POST":
        form = RLCSeriesForm(request.POST)
        if form.is_valid():
            R = float(form.cleaned_data["R"])
            L = float(form.cleaned_data["L"])
            C = float(form.cleaned_data["C"])
            V0 = float(form.cleaned_data["V0"])
            q0 = float(form.cleaned_data["q0"])
            i0 = float(form.cleaned_data["i0"])
            t_end = float(form.cleaned_data["t_end"])
            dt = float(form.cleaned_data["dt"])

            t, q, i, Vc = _solve_rlc_series(R, L, C, V0, q0, i0, t_end, dt)

            fig1 = plt.figure()
            plt.plot(t, q)
            plt.xlabel("t (s)")
            plt.ylabel("q (C)")
            plt.title("RLC: zaryad q(t)")
            img_q = _plot_to_base64(fig1)

            fig2 = plt.figure()
            plt.plot(t, i)
            plt.xlabel("t (s)")
            plt.ylabel("i (A)")
            plt.title("RLC: tok i(t)")
            img_i = _plot_to_base64(fig2)

            fig3 = plt.figure()
            plt.plot(t, Vc)
            plt.xlabel("t (s)")
            plt.ylabel("Vc (V)")
            plt.title("RLC: kondensator kuchlanishi Vc(t)")
            img_vc = _plot_to_base64(fig3)

            stats = {
                "q_min": float(np.min(q)),
                "q_max": float(np.max(q)),
                "i_min": float(np.min(i)),
                "i_max": float(np.max(i)),
                "vc_min": float(np.min(Vc)),
                "vc_max": float(np.max(Vc)),
            }

            conclusion = _build_conclusion_rlc(R, L, C, V0, q, i, Vc)

            # ---------- 3D Surface (faqat UI) ----------
            R_min, R_max = _safe_center_range(R, default_min=0.5, default_max=50.0, factor_min=0.25, factor_max=2.0)
            R_steps = int(request.POST.get("R_steps", 25))
            z_mode = (request.POST.get("z_mode", "I") or "I").strip().upper()
            if z_mode not in ("I", "VC"):
                z_mode = "I"

            surface_div = _build_rlc_surface_div(
                R_center=R, L=L, C=C, V0=V0, q0=q0, i0=i0,
                t_end=t_end, dt=dt,
                R_min=R_min, R_max=R_max, R_steps=R_steps,
                z_mode=z_mode
            )
    else:
        form = RLCSeriesForm()

    return render(request, "ai_module/rlc_series.html", {
        "form": form,
        "img_q": img_q,
        "img_i": img_i,
        "img_vc": img_vc,
        "stats": stats,
        "conclusion": conclusion,
        "surface_div": surface_div,  # <-- YANGI
        "scipy_ok": SCIPY_OK,
    })


def rlc_pdf_view(request):
    def _p(key, default):
        v = request.GET.get(key) or request.POST.get(key)
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return default

    R = _p("R", 5.0)
    L = _p("L", 0.5)
    C = _p("C", 0.01)
    V0 = _p("V0", 10.0)
    q0 = _p("q0", 0.0)
    i0 = _p("i0", 0.0)
    t_end = _p("t_end", 10.0)
    dt = _p("dt", 0.001)

    t, q, i, Vc = _solve_rlc_series(R, L, C, V0, q0, i0, t_end, dt)
    conclusion = _build_conclusion_rlc(R, L, C, V0, q, i, Vc)

    imgs = []
    for (title, ydata, ylabel) in [
        ("Zaryad q(t)", q, "q (C)"),
        ("Tok i(t)", i, "i (A)"),
        ("Kondensator kuchlanishi Vc(t)", Vc, "Vc (V)"),
    ]:
        fig = plt.figure()
        plt.plot(t, ydata)
        plt.xlabel("t (s)")
        plt.ylabel(ylabel)
        plt.title(title)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)
    _pdf_header(cpdf, "RLC zanjiri — PDF hisobot")
    _pdf_params_block(cpdf, [
        ("R (Ohm)", f"{R:g}"), ("L (H)", f"{L:g}"), ("C (F)", f"{C:g}"),
        ("V0 (V)", f"{V0:g}"), ("q0 (C)", f"{q0:g}"), ("i0 (A)", f"{i0:g}"),
        ("T (s)", f"{t_end:g}"), ("dt (s)", f"{dt:g}"),
    ], y=27.2*cm)

    x0_pdf, w, h, y_top = 2*cm, 17.0*cm, 5.8*cm, 22.0*cm
    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h + 0.5*cm)
        cpdf.drawImage(ImageReader(img_buf), x0_pdf, y - h, width=w, height=h, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, conclusion)
    _pdf_page_number(cpdf, 1)
    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="RLC_natijalar.pdf"'
    return resp


# =========================
#  ERKIN TUSHISH + Havo qarshiligi
# =========================
def _solve_free_fall_drag(m, g, k, drag_type, y0, v0, t_end, dt):
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    def acc(v):
        if drag_type == "linear":
            return g - (k / m) * v
        return g - (k / m) * v * abs(v)

    def f(_t, Y):
        y, v = Y
        return [v, acc(v)]

    if SCIPY_OK:
        sol = solve_ivp(
            f, (0.0, t_end), [0.0, v0], t_eval=t,
            method="RK45", rtol=1e-6, atol=1e-9
        )
        y = sol.y[0]
        v = sol.y[1]
    else:
        y = np.zeros_like(t)
        v = np.zeros_like(t)
        y[0] = 0.0
        v[0] = v0

        for i in range(len(t) - 1):
            h = dt
            ti = t[i]
            yi = np.array([y[i], v[i]])

            k1 = np.array(f(ti, yi))
            k2 = np.array(f(ti + h / 2, yi + h * k1 / 2))
            k3 = np.array(f(ti + h / 2, yi + h * k2 / 2))
            k4 = np.array(f(ti + h, yi + h * k3))

            yi_next = yi + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            y[i + 1] = yi_next[0]
            v[i + 1] = yi_next[1]

    hgt = y0 - y
    a = np.array([acc(vi) for vi in v], dtype=float)

    hit_idx = None
    for i in range(len(t)):
        if hgt[i] <= 0:
            hit_idx = i
            break

    if hit_idx is not None and hit_idx > 0:
        t = t[: hit_idx + 1]
        y = y[: hit_idx + 1]
        v = v[: hit_idx + 1]
        hgt = hgt[: hit_idx + 1]
        a = a[: hit_idx + 1]

    return t, y, hgt, v, a


def _build_conclusion_free_fall(m, g, k, drag_type, y0, v0, t, hgt, v, a):
    if k <= 0:
        v_term = None
        drag_txt = "Qarshilik yo‘q (k=0), erkin tushish ideal holatga yaqin."
    else:
        if drag_type == "linear":
            v_term = m * g / k
        else:
            v_term = (m * g / k) ** 0.5
        drag_txt = f"Qarshilik turi: {'chiziqli (k·v)' if drag_type=='linear' else 'kvadratik (k·v²)'}."

    landed = (hgt[-1] <= 0)
    t_land = float(t[-1]) if landed else None
    v_end = float(v[-1])
    a_end = float(a[-1])

    txt = f"{drag_txt} m={m}, g={g}, k={k}, y0={y0}, v0={v0}. "
    if v_term is not None:
        txt += f"Terminal tezlik vₜ≈{v_term:.3f} m/s. "

    if landed:
        txt += f"Jism yerga t≈{t_land:.3f} s da yetib keldi. v≈{v_end:.3f} m/s, a≈{a_end:.3f} m/s²."
    else:
        txt += "Berilgan T vaqt oralig‘ida yerga yetib bormadi; T ni oshirib qayta hisoblash tavsiya etiladi."

    return txt


def _build_free_fall_surface_div(m, g, k_center, drag_type, y0, v0, t_end, dt, k_min, k_max, k_steps, z_mode):
    """
    3D Surface (Erkin tushish + drag):
      X = t
      Y = k (qarshilik koeff.)
      Z = h(t) yoki v(t)

    z_mode: "H" yoki "V"
    """
    k_steps = int(max(10, k_steps))
    k_vals = np.linspace(float(k_min), float(k_max), k_steps, dtype=float)
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    Z = np.zeros((len(k_vals), len(t)), dtype=float)
    for i, k in enumerate(k_vals):
        tt, y, hgt, v, a = _solve_free_fall_drag(float(m), float(g), float(k), drag_type, float(y0), float(v0), float(t_end), float(dt))
        # Agar yerga urilishi bilan kesilgan bo‘lsa, tt uzunligi qisqaroq bo‘lishi mumkin.
        # Surface uchun matritsa barqaror bo‘lishi kerak => t_end oralig‘ida kesmaymiz: hgt/v ni t ga qayta joylaymiz.
        # Yechim: kesilmagan "to‘liq" hisobni majburlash uchun shu yerda hit-cut qilmasdan hisoblaymiz.
        # Bizda _solve_free_fall_drag kesadi, shuning uchun padding qilamiz.
        zz = hgt if z_mode == "H" else v
        if len(zz) < len(t):
            pad = np.full((len(t) - len(zz),), zz[-1], dtype=float)
            zz = np.concatenate([zz, pad], axis=0)
        Z[i, :] = zz[:len(t)]

    z_title = "h(t) (m)" if z_mode == "H" else "v(t) (m/s)"

    fig = go.Figure(data=[go.Surface(x=t, y=k_vals, z=Z)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="k",
            zaxis_title=z_title,
        ),
    )
    return plot(fig, output_type="div", include_plotlyjs=True)


def free_fall_view(request):
    img_h = img_v = img_a = None
    stats = None
    conclusion = None
    surface_div = None  # <-- YANGI (UI 3D)

    if request.method == "POST":
        form = FreeFallDragForm(request.POST)
        if form.is_valid():
            m = float(form.cleaned_data["m"])
            g = float(form.cleaned_data["g"])
            drag_type = form.cleaned_data["drag_type"]
            k = float(form.cleaned_data["k"])
            y0 = float(form.cleaned_data["y0"])
            v0 = float(form.cleaned_data["v0"])
            t_end = float(form.cleaned_data["t_end"])
            dt = float(form.cleaned_data["dt"])

            t, y, hgt, v, a = _solve_free_fall_drag(m, g, k, drag_type, y0, v0, t_end, dt)

            fig1 = plt.figure()
            plt.plot(t, hgt)
            plt.xlabel("t (s)")
            plt.ylabel("h (m)")
            plt.title("Balandlik h(t) = y0 - y(t)")
            img_h = _plot_to_base64(fig1)

            fig2 = plt.figure()
            plt.plot(t, v)
            plt.xlabel("t (s)")
            plt.ylabel("v (m/s)")
            plt.title("Tezlik v(t)")
            img_v = _plot_to_base64(fig2)

            fig3 = plt.figure()
            plt.plot(t, a)
            plt.xlabel("t (s)")
            plt.ylabel("a (m/s²)")
            plt.title("Tezlanish a(t)")
            img_a = _plot_to_base64(fig3)

            stats = {
                "h_min": float(np.min(hgt)),
                "h_max": float(np.max(hgt)),
                "v_min": float(np.min(v)),
                "v_max": float(np.max(v)),
                "a_min": float(np.min(a)),
                "a_max": float(np.max(a)),
                "t_end_real": float(t[-1]),
            }

            conclusion = _build_conclusion_free_fall(m, g, k, drag_type, y0, v0, t, hgt, v, a)

            # ---------- 3D Surface (faqat UI) ----------
            k_min, k_max = _safe_center_range(k, default_min=0.1, default_max=2.0, factor_min=0.25, factor_max=2.0)
            k_steps = int(request.POST.get("k_steps", 25))
            z_mode = (request.POST.get("z_mode", "H") or "H").strip().upper()
            if z_mode not in ("H", "V"):
                z_mode = "H"

            surface_div = _build_free_fall_surface_div(
                m=m, g=g, k_center=k, drag_type=drag_type, y0=y0, v0=v0,
                t_end=t_end, dt=dt,
                k_min=k_min, k_max=k_max, k_steps=k_steps,
                z_mode=z_mode
            )
    else:
        form = FreeFallDragForm()

    return render(request, "ai_module/free_fall.html", {
        "form": form,
        "img_h": img_h,
        "img_v": img_v,
        "img_a": img_a,
        "stats": stats,
        "conclusion": conclusion,
        "surface_div": surface_div,  # <-- YANGI
        "scipy_ok": SCIPY_OK,
    })


def free_fall_pdf_view(request):
    def _p(key, default):
        v = request.GET.get(key) or request.POST.get(key)
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return default

    m = _p("m", 70.0)
    g = _p("g", 9.81)
    k = _p("k", 0.5)
    y0 = _p("y0", 1000.0)
    v0 = _p("v0", 0.0)
    t_end = _p("t_end", 30.0)
    dt = _p("dt", 0.05)
    drag_type = (request.GET.get("drag_type") or request.POST.get("drag_type") or "linear").strip()

    t, _y, hgt, v, a = _solve_free_fall_drag(m, g, k, drag_type, y0, v0, t_end, dt)
    conclusion = _build_conclusion_free_fall(m, g, k, drag_type, y0, v0, t, hgt, v, a)

    imgs = []
    for (title, ydata, ylabel) in [
        ("Balandlik h(t)", hgt, "h (m)"),
        ("Tezlik v(t)", v, "v (m/s)"),
        ("Tezlanish a(t)", a, "a (m/s²)"),
    ]:
        fig = plt.figure()
        plt.plot(t, ydata)
        plt.xlabel("t (s)")
        plt.ylabel(ylabel)
        plt.title(title)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)
    _pdf_header(cpdf, "Erkin tushish — PDF hisobot")
    _pdf_params_block(cpdf, [
        ("m (kg)", f"{m:g}"), ("g (m/s²)", f"{g:g}"), ("k", f"{k:g}"),
        ("Qarshilik turi", drag_type), ("h0 (m)", f"{y0:g}"),
        ("v0 (m/s)", f"{v0:g}"), ("T (s)", f"{t_end:g}"), ("dt (s)", f"{dt:g}"),
    ], y=27.2*cm)

    x0_pdf, w, h_img, y_top = 2*cm, 17.0*cm, 5.8*cm, 22.0*cm
    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h_img + 0.5*cm)
        cpdf.drawImage(ImageReader(img_buf), x0_pdf, y - h_img, width=w, height=h_img, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, conclusion)
    _pdf_page_number(cpdf, 1)
    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="FreeFall_drag_natijalar.pdf"'
    return resp


# =========================
#  RADIOAKTIV PARCHALANISH + 3D SURFACE (Plotly)
# =========================
def _solve_decay(N0, lam, t_end, dt):
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    def f(_t, y):
        return [-lam * y[0]]

    if SCIPY_OK:
        sol = solve_ivp(f, (0.0, t_end), [N0], t_eval=t, rtol=1e-7, atol=1e-10)
        N = sol.y[0]
    else:
        N = np.zeros_like(t)
        N[0] = N0
        for i in range(len(t) - 1):
            h = dt
            Ni = N[i]
            k1 = -lam * Ni
            k2 = -lam * (Ni + h * k1 / 2)
            k3 = -lam * (Ni + h * k2 / 2)
            k4 = -lam * (Ni + h * k3)
            N[i + 1] = Ni + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

    A = lam * N
    return t, N, A


def _build_conclusion_decay(N0, lam, t_end):
    if lam <= 0:
        return "λ ≤ 0 bo‘lgani uchun model fizik ma’noga ega emas. λ > 0 tanlang."

    T12 = np.log(2.0) / lam
    N_end = N0 * np.exp(-lam * t_end)
    return (
        "Radioaktiv parchalanish modeli dN/dt = −λN bo‘yicha yechildi. "
        f"λ={lam} 1/s bo‘lganda yarim yemirilish vaqti T₁/₂=ln(2)/λ ≈ {T12:.4f} s. "
        f"t={t_end} s da nazariy hisobda N(t) ≈ {N_end:.3f}. "
        "Model natijalari N(t) eksponensial kamayishini va aktivlik A(t)=λN(t) ham mos ravishda pasayishini ko‘rsatadi."
    )


def _build_decay_surface_div(N0, t_end, dt, lam_min, lam_max, lam_steps, z_mode):
    """
    3D Surface:
      X = t, Y = λ, Z = N(t) yoki A(t)
    """
    lam_steps = int(max(5, lam_steps))
    lam_vals = np.linspace(float(lam_min), float(lam_max), lam_steps, dtype=float)
    t = np.arange(0.0, t_end + dt, dt, dtype=float)

    Z = np.zeros((len(lam_vals), len(t)), dtype=float)
    for i, lam in enumerate(lam_vals):
        _, N, A = _solve_decay(N0, float(lam), t_end, dt)
        Z[i, :] = A if z_mode == "A" else N

    z_title = "A(t)=λN(t)" if z_mode == "A" else "N(t)"

    fig = go.Figure(data=[go.Surface(x=t, y=lam_vals, z=Z)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="λ (1/s)",
            zaxis_title=z_title,
        ),
    )
    return plot(fig, output_type="div", include_plotlyjs=True)


def decay_view(request):
    img_N = img_A = img_lnN = None
    stats = None
    conclusion = None
    surface_div = None

    # 3D defaultlar
    lam_min_default = 0.1
    lam_max_default = 2.0
    lam_steps_default = 25
    z_mode_default = "N"  # N yoki A

    if request.method == "POST":
        form = RadioactiveDecayForm(request.POST)
        if form.is_valid():
            N0 = float(form.cleaned_data["N0"])
            lam = float(form.cleaned_data["lam"])
            t_end = float(form.cleaned_data["t_end"])
            dt = float(form.cleaned_data["dt"])

            t, N, A = _solve_decay(N0, lam, t_end, dt)

            fig1 = plt.figure(figsize=(7.2, 3.2))
            plt.plot(t, N)
            plt.xlabel("t (s)")
            plt.ylabel("N(t)")
            plt.title("Zarrachalar soni N(t)")
            img_N = _plot_to_base64(fig1)

            fig2 = plt.figure(figsize=(7.2, 3.2))
            plt.plot(t, A)
            plt.xlabel("t (s)")
            plt.ylabel("A(t)")
            plt.title("Aktivlik A(t)=λN(t)")
            img_A = _plot_to_base64(fig2)

            eps = 1e-12
            fig3 = plt.figure(figsize=(7.2, 3.2))
            plt.plot(t, np.log(np.maximum(N, eps)))
            plt.xlabel("t (s)")
            plt.ylabel("ln(N)")
            plt.title("ln(N) — chiziqli ko‘rinish (tekshiruv)")
            img_lnN = _plot_to_base64(fig3)

            T12 = float(np.log(2.0) / lam) if lam > 0 else None
            stats = {
                "T12": T12,
                "N_end": float(N[-1]),
                "A_end": float(A[-1]),
                "t_end_real": float(t[-1]),
            }

            conclusion = _build_conclusion_decay(N0, lam, t_end)

            # 3D parametrlari (UI formga qo‘shmasangiz ham ishlaydi)
            lam_min = float(request.POST.get("lam_min", lam_min_default))
            lam_max = float(request.POST.get("lam_max", lam_max_default))
            lam_steps = int(request.POST.get("lam_steps", lam_steps_default))
            z_mode = (request.POST.get("z_mode", z_mode_default) or "N").strip().upper()
            if z_mode not in ("N", "A"):
                z_mode = "N"
            if lam_max <= lam_min:
                lam_max = lam_min + 0.1

            surface_div = _build_decay_surface_div(
                N0=N0, t_end=t_end, dt=dt,
                lam_min=lam_min, lam_max=lam_max, lam_steps=lam_steps,
                z_mode=z_mode,
            )
    else:
        form = RadioactiveDecayForm()

    return render(request, "ai_module/decay.html", {
        "form": form,
        "img_N": img_N,
        "img_A": img_A,
        "img_lnN": img_lnN,
        "stats": stats,
        "conclusion": conclusion,
        "surface_div": surface_div,  # <-- 3D
        "scipy_ok": SCIPY_OK,
    })


def decay_pdf_view(request):
    def _p(key, default):
        v = request.GET.get(key) or request.POST.get(key)
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return default

    N0 = _p("N0", 1000.0)
    lam = _p("lam", 0.5)
    t_end = _p("t_end", 10.0)
    dt = _p("dt", 0.05)

    t, N, A = _solve_decay(N0, lam, t_end, dt)
    lnN = np.log(np.maximum(N, 1e-300))
    conclusion = _build_conclusion_decay(N0, lam, t_end)

    imgs = []
    for (title, ydata, ylabel) in [
        ("Atom soni N(t)", N, "N(t)"),
        ("Faollik A(t)", A, "A(t)"),
        ("ln N(t)", lnN, "ln N"),
    ]:
        fig = plt.figure()
        plt.plot(t, ydata)
        plt.xlabel("t (s)")
        plt.ylabel(ylabel)
        plt.title(title)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)
    _pdf_header(cpdf, "Radioaktiv parchalanish — PDF hisobot")
    _pdf_params_block(cpdf, [
        ("N0 (boshlang'ich)", f"{N0:g}"), ("λ (parchalanish doimiysi)", f"{lam:g}"),
        ("T (s)", f"{t_end:g}"), ("dt (s)", f"{dt:g}"),
    ], y=27.2*cm)

    x0_pdf, w, h_img, y_top = 2*cm, 17.0*cm, 5.8*cm, 22.0*cm
    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h_img + 0.5*cm)
        cpdf.drawImage(ImageReader(img_buf), x0_pdf, y - h_img, width=w, height=h_img, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, conclusion)
    _pdf_page_number(cpdf, 1)
    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="RadioactiveDecay_natijalar.pdf"'
    return resp

# ===================================================================
# 1D issiqlik (Fourier) – XULOSA generatsiyasi
# ===================================================================
def _build_conclusion_heat(alpha, L, tmax, nx, nt, ic_type, amp, x0, sigma,
                           T_left, T_right, T_mat, x, t):
    dx = x[1] - x[0]
    maxT  = float(np.max(T_mat))
    minT  = float(np.min(T_mat))
    meanT = float(np.mean(T_mat))
    T_mid_0   = float(T_mat[0, nx//2])
    T_mid_end = float(T_mat[-1, nx//2])
    t_diff = L**2 / (np.pi**2 * alpha)

    base = (
        f"Berilgan 1D issiqlik tenglamasi ∂T/∂t = α ∂²T/∂x² (α = {alpha} m²/s) "
        f"uchun diskret modelda nx={nx}, nt={nt}, L={L} m, tmax={tmax} s "
        f"parametrlari bilan hisoblar olib borildi. "
        f"Boshlang‘ich shart: {ic_type} (amp={amp}, x₀={x0}, σ={sigma}). "
        f"Chegaralar: T(0,t)={T_left} °C, T(L,t)={T_right} °C. "
    )

    stats = (
        f"Natijaga ko‘ra T_max={maxT:.3f} °C, T_min={minT:.3f} °C, T_ort={meanT:.3f} °C. "
        f"O‘rtacha nuqtada T(t=0)={T_mid_0:.3f} °C, T(t={tmax})={T_mid_end:.3f} °C. "
    )

    diff = (
        f"Diffuziya vaqti taxminan t_diff≈{t_diff:.3f} s, "
        f"ya‘ni tizim muvozanatga yaqinlashish vaqti shu bilan aniqlanadi. "
        f"Model natijalari fizik ma’qul va kutilgan eksponensial yumshoq profil ko‘rsatdi."
    )

    return base + stats + diff


# ============================================================
# 1-MASALA: Fourier (1D Heat Equation) — UI View (FIXED)
# ============================================================
def heat_fourier_view(request):
    import json
    import numpy as np
    import matplotlib.pyplot as plt
    from django.shortcuts import render

    # solve_ivp / SCIPY_OK sizda oldin bor (global yoki import qilingan deb hisoblayman)
    # _plot_to_base64, _build_conclusion_heat ham sizda bor

    defaults = {
        "L": 1.0,
        "alpha": 0.2,
        "nx": 40,
        "tmax": 1.0,
        "nt": 60,
        "T_left": 0.0,
        "T_right": 0.0,
        "ic_type": "sine",
        "amp": 1.0,
        "x0": 0.35,
        "sigma": 0.08,
    }

    src = request.GET
    data = defaults.copy()

    def _get_float(key):
        try:
            return float(src.get(key, data[key]))
        except Exception:
            return float(data[key])

    def _get_int(key):
        try:
            return int(src.get(key, data[key]))
        except Exception:
            return int(data[key])

    # --- read inputs ---
    data["L"] = _get_float("L")
    data["alpha"] = _get_float("alpha")
    data["nx"] = max(10, _get_int("nx"))
    data["tmax"] = max(0.05, _get_float("tmax"))
    data["nt"] = max(10, _get_int("nt"))
    data["T_left"] = _get_float("T_left")
    data["T_right"] = _get_float("T_right")
    data["ic_type"] = str(src.get("ic_type", data["ic_type"])).strip().lower()
    data["amp"] = _get_float("amp")
    data["x0"] = _get_float("x0")
    data["sigma"] = max(1e-4, _get_float("sigma"))

    L = data["L"]
    nx = data["nx"]
    alpha = data["alpha"]
    tmax = data["tmax"]
    nt = data["nt"]
    T_left = data["T_left"]
    T_right = data["T_right"]

    x = np.linspace(0.0, L, nx)
    dx = x[1] - x[0]

    ic_type = data["ic_type"]
    amp = data["amp"]
    x0 = data["x0"]
    sigma = data["sigma"]

    # --- initial condition ---
    if ic_type == "gaussian":
        T0 = amp * np.exp(-0.5 * ((x - x0) / sigma) ** 2)
    elif ic_type == "step":
        T0 = amp * (x >= x0).astype(float)
    else:
        ic_type = "sine"  # fallback
        data["ic_type"] = "sine"
        T0 = amp * np.sin(np.pi * x / L)

    # enforce boundaries
    T0[0] = T_left
    T0[-1] = T_right

    # --- PDE -> ODE system (interior points only) ---
    def rhs(t, y):
        T = np.empty(nx, dtype=float)
        T[0] = T_left
        T[-1] = T_right
        T[1:-1] = y
        d2 = (T[2:] - 2.0 * T[1:-1] + T[:-2]) / (dx * dx)
        return alpha * d2

    y0 = T0[1:-1].copy()
    t_eval = np.linspace(0.0, tmax, nt)

    sol = solve_ivp(
        rhs,
        t_span=(0.0, tmax),
        y0=y0,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8
    )

    # --- reconstruct full temperature matrix ---
    T_mat = np.zeros((len(sol.t), nx), dtype=float)
    T_mat[:, 0] = T_left
    T_mat[:, -1] = T_right
    T_mat[:, 1:-1] = sol.y.T  # shape: (nt, nx-2)

    # ============================================================
    # 2D plots (Matplotlib)
    # ============================================================
    fig1 = plt.figure(figsize=(6, 3))
    ax1 = fig1.add_subplot(111)
    idxs = [0, len(sol.t)//3, 2*len(sol.t)//3, len(sol.t)-1]
    idxs = sorted(list(set([i for i in idxs if 0 <= i < len(sol.t)])))
    for i in idxs:
        ax1.plot(x, T_mat[i, :], label=f"t={sol.t[i]:.3f}")
    ax1.set_xlabel("x (m)")
    ax1.set_ylabel("T (°C)")
    ax1.set_title("T(x,t) – tanlangan vaqtlar")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    plot_tx_base64 = _plot_to_base64(fig1)

    mid_j = nx // 2
    fig2 = plt.figure(figsize=(6, 3))
    ax2 = fig2.add_subplot(111)
    ax2.plot(sol.t, T_mat[:, mid_j])
    ax2.set_xlabel("t (s)")
    ax2.set_ylabel(f"T(x={x[mid_j]:.3f}, t) (°C)")
    ax2.set_title("O‘rtadagi nuqtada T(t)")
    ax2.grid(True, alpha=0.3)
    plot_tmid_base64 = _plot_to_base64(fig2)

    # ============================================================
    # ✅ Plotly 3D payload (FIX)
    # Plotly.newPlot('surface3d', payload.data, payload.layout, ...)
    # ============================================================
    # Meshgrid: X, TT -> shape (nt, nx)
    X, TT = np.meshgrid(x, sol.t)

    plotly_payload = {
        "data": [{
            "type": "surface",
            "x": X.tolist(),
            "y": TT.tolist(),
            "z": T_mat.tolist(),
            # ixtiyoriy: rang sxemasi
            "colorscale": "Viridis",
            "showscale": True,
            "hovertemplate": "x=%{x:.4f}<br>t=%{y:.4f}<br>T=%{z:.4f}<extra></extra>",
        }],
        "layout": {
            "title": "3D Sirt: T(x,t)",
            "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
            "scene": {
                "xaxis": {"title": "x (m)"},
                "yaxis": {"title": "t (s)"},
                "zaxis": {"title": "T (°C)"},
                # ixtiyoriy: kamera
                "camera": {"eye": {"x": 1.4, "y": 1.3, "z": 0.9}},
            }
        }
    }

    # stats + conclusion
    stats = {
        "T_max": float(np.max(T_mat)),
        "T_min": float(np.min(T_mat)),
        "T_avg": float(np.mean(T_mat)),
    }

    conclusion = _build_conclusion_heat(
        alpha, L, tmax, nx, nt, ic_type, amp, x0, sigma,
        T_left, T_right, T_mat, x, sol.t
    )

    context = {
        "page_title": "Fourier issiqlik | DiffPhys",
        "form": data,
        "plot_tx_base64": plot_tx_base64,
        "plot_tmid_base64": plot_tmid_base64,

        # ✅ JSON sifatida yuboramiz (template: const payload = {{ plotly_payload|safe }})
        "plotly_payload": json.dumps(plotly_payload),

        "conclusion": conclusion,
        "stats": stats,
        "scipy_ok": SCIPY_OK,
    }
    return render(request, "ai_module/heat_fourier.html", context)

# ============================================================
# 1D issiqlik – PDF View (POST orqali)
# ============================================================
def heat_fourier_pdf_view(request):
    def _gp(key, default):
        v = request.GET.get(key) or request.POST.get(key)
        return v if v is not None and str(v).strip() != "" else default

    def _fp(key, default):
        try:
            return float(str(_gp(key, default)).replace(",", "."))
        except Exception:
            return default

    def _ip(key, default):
        try:
            return max(int(float(str(_gp(key, default)))), 1)
        except Exception:
            return default

    L = _fp("L", 1.0)
    alpha = _fp("alpha", 0.2)
    nx = max(10, _ip("nx", 40))
    tmax = max(0.05, _fp("tmax", 1.0))
    nt = max(10, _ip("nt", 60))
    T_left = _fp("T_left", 0.0)
    T_right = _fp("T_right", 0.0)
    ic_type = str(_gp("ic_type", "sine")).strip().lower()
    amp = _fp("amp", 1.0)
    x0_ic = _fp("x0", 0.35)
    sigma = max(1e-4, _fp("sigma", 0.08))

    x = np.linspace(0.0, L, nx)
    dx = x[1] - x[0]

    if ic_type == "gaussian":
        T0 = amp * np.exp(-0.5 * ((x - x0_ic) / sigma) ** 2)
    elif ic_type == "step":
        T0 = amp * (x >= x0_ic).astype(float)
    else:
        ic_type = "sine"
        T0 = amp * np.sin(np.pi * x / L)
    T0[0] = T_left
    T0[-1] = T_right

    def rhs(ti, y):
        T = np.empty(nx, dtype=float)
        T[0] = T_left
        T[-1] = T_right
        T[1:-1] = y
        d2 = (T[2:] - 2.0 * T[1:-1] + T[:-2]) / (dx * dx)
        return alpha * d2

    y0 = T0[1:-1].copy()
    t_eval = np.linspace(0.0, tmax, nt)
    sol = solve_ivp(rhs, (0.0, tmax), y0, t_eval=t_eval, method="RK45", rtol=1e-6, atol=1e-8)

    T_mat = np.zeros((len(sol.t), nx), dtype=float)
    T_mat[:, 0] = T_left
    T_mat[:, -1] = T_right
    T_mat[:, 1:-1] = sol.y.T

    conclusion = _build_conclusion_heat(alpha, L, tmax, nx, nt, ic_type, amp, x0_ic, sigma,
                                        T_left, T_right, T_mat, x, sol.t)

    imgs = []
    fig1 = plt.figure(figsize=(6, 3))
    ax1 = fig1.add_subplot(111)
    idxs = sorted(list(set([0, len(sol.t)//3, 2*len(sol.t)//3, len(sol.t)-1])))
    for i in [j for j in idxs if 0 <= j < len(sol.t)]:
        ax1.plot(x, T_mat[i, :], label=f"t={sol.t[i]:.3f}")
    ax1.set_xlabel("x (m)")
    ax1.set_ylabel("T (°C)")
    ax1.set_title("T(x,t) – tanlangan vaqtlar")
    ax1.legend()
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig1)
    buf1.seek(0)
    imgs.append(buf1)

    mid_j = nx // 2
    fig2 = plt.figure(figsize=(6, 3))
    ax2 = fig2.add_subplot(111)
    ax2.plot(sol.t, T_mat[:, mid_j])
    ax2.set_xlabel("t (s)")
    ax2.set_ylabel(f"T(x={x[mid_j]:.3f}, t) (°C)")
    ax2.set_title("O'rtadagi nuqtada T(t)")
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig2)
    buf2.seek(0)
    imgs.append(buf2)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)
    _pdf_header(cpdf, "Fourier issiqlik tenglamasi — PDF hisobot")
    _pdf_params_block(cpdf, [
        ("L (m)", f"{L:g}"), ("α (m²/s)", f"{alpha:g}"), ("nx", f"{nx}"),
        ("tmax (s)", f"{tmax:g}"), ("nt", f"{nt}"), ("T_left", f"{T_left:g}"),
        ("T_right", f"{T_right:g}"), ("IC turi", ic_type),
    ], y=27.2*cm)

    x0_pdf, w, h_img, y_top = 2*cm, 17.0*cm, 7.0*cm, 22.5*cm
    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h_img + 0.8*cm)
        cpdf.drawImage(ImageReader(img_buf), x0_pdf, y - h_img, width=w, height=h_img, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, conclusion)
    _pdf_page_number(cpdf, 1)
    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="heat_fourier_report.pdf"'
    return resp




# ---------------------------
# yordamchi: matplotlib -> base64
# ---------------------------
def _plot_to_base64(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _build_conclusion_osc(m, k, c, x0, v0, tmax):
    w0 = np.sqrt(k / m)
    zeta = c / (2 * np.sqrt(k * m))

    if c == 0:
        regime = "Undamped (so‘nmas tebranish)"
    else:
        if zeta < 1:
            regime = "Underdamped (so‘nuvchi tebranish)"
        elif abs(zeta - 1) < 1e-6:
            regime = "Critically damped (kritik so‘nish)"
        else:
            regime = "Overdamped (ortiqcha so‘nish, tebranishsiz)"

    return (
        f"m={m}, k={k}, c={c} uchun tizim rejimi: {regime}. "
        f"Boshlang‘ich shartlar x(0)={x0}, v(0)={v0}. "
        f"Tahlil oralig‘i: 0…{tmax} s. "
        f"Tabiiy burchak tezlik ω0=√(k/m)≈{w0:.4f}, so‘nish koeffitsienti ζ≈{zeta:.4f}."
    )


# ============================================================
# 2-MASALA: Prujina–massa (damped/undamped) — UI View (MassSpring2)
#   - horizontal/vertical rejim
#   - damping ratio (zeta), omega0, regime tahlili
#   - x_eq = mg/k (vertical)
#   - x(t), v(t), a(t) + Plotly 3D (x~, v, t)
# ============================================================
def mass_spring2_view(request):
    import json

    defaults = {
        "mode": "horizontal",  # horizontal | vertical
        "g": 9.81,             # m/s^2 (faqat vertical)
        "m": 1.0,              # kg
        "k": 20.0,             # N/m
        "c": 0.0,              # N*s/m  (0 -> undamped)
        "x0": 0.15,            # m (absolute x)
        "v0": 0.0,             # m/s
        "tmax": 10.0,          # s
        "nt": 600,             # nuqtalar soni
    }

    src = request.GET
    data = defaults.copy()

    def _get_float(key):
        try:
            return float(src.get(key, data[key]))
        except Exception:
            return float(data[key])

    def _get_int(key):
        try:
            return int(src.get(key, data[key]))
        except Exception:
            return int(data[key])

    # ---- inputs
    data["mode"] = str(src.get("mode", data["mode"])).strip().lower()
    if data["mode"] not in ("horizontal", "vertical"):
        data["mode"] = "horizontal"

    data["g"] = max(0.0, _get_float("g"))
    data["m"] = max(1e-9, _get_float("m"))
    data["k"] = max(1e-9, _get_float("k"))
    data["c"] = max(0.0, _get_float("c"))
    data["x0"] = _get_float("x0")
    data["v0"] = _get_float("v0")
    data["tmax"] = max(0.05, _get_float("tmax"))
    data["nt"] = max(50, _get_int("nt"))

    mode = data["mode"]
    g = data["g"]
    m = data["m"]
    k = data["k"]
    c = data["c"]
    x0 = data["x0"]
    v0 = data["v0"]
    tmax = data["tmax"]
    nt = data["nt"]

    # ============================================================
    # Fizik tahlil (mass_spring2 ga xos)
    # ============================================================
    omega0 = float(np.sqrt(k / m))  # tabiiy chastota
    zeta = float(c / (2.0 * np.sqrt(m * k))) if (m > 0 and k > 0) else 0.0

    if c == 0.0:
        regime = "undamped (so‘nishsiz)"
    else:
        if zeta < 1.0:
            regime = "underdamped (tebranish so‘nadi)"
        elif abs(zeta - 1.0) < 1e-6:
            regime = "critical damping (kritik so‘nish)"
        else:
            regime = "overdamped (tebranmasdan qaytish)"

    # Vertical holatda muvozanat siljishi:
    # m x'' + c x' + k x = m g  ->  x_eq = m g / k
    x_eq = float(m * g / k) if (mode == "vertical") else 0.0

    # x~ = x - x_eq (muvozanatga nisbatan siljish)
    x_tilde0 = float(x0 - x_eq)

    # ============================================================
    # ODE: x~'' + (c/m) x~' + (k/m) x~ = 0
    # ============================================================
    def rhs(t, y):
        xt, v = y
        dxt = v
        dv = -(c / m) * v - (k / m) * xt
        return [dxt, dv]

    t_eval = np.linspace(0.0, tmax, nt)

    # SciPy bo'lmasa — fallback RK4
    if SCIPY_OK and solve_ivp is not None:
        sol = solve_ivp(
            rhs,
            (0.0, tmax),
            [x_tilde0, v0],
            t_eval=t_eval,
            rtol=1e-7,
            atol=1e-9,
            method="RK45",
        )
        t = sol.t
        x_tilde = sol.y[0]
        v = sol.y[1]
    else:
        # RK4 fallback
        t = t_eval
        dt = float(t[1] - t[0])
        x_tilde = np.zeros_like(t, dtype=float)
        v = np.zeros_like(t, dtype=float)
        x_tilde[0] = x_tilde0
        v[0] = v0

        for i in range(len(t) - 1):
            y = np.array([x_tilde[i], v[i]], dtype=float)

            k1 = np.array(rhs(t[i], y))
            k2 = np.array(rhs(t[i] + dt / 2, y + dt * k1 / 2))
            k3 = np.array(rhs(t[i] + dt / 2, y + dt * k2 / 2))
            k4 = np.array(rhs(t[i] + dt, y + dt * k3))

            y_next = y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            x_tilde[i + 1] = y_next[0]
            v[i + 1] = y_next[1]

    # Absolute x (agar vertical bo‘lsa)
    x = x_tilde + x_eq

    # tezlanish (x~ bo‘yicha)
    a = -(c / m) * v - (k / m) * x_tilde

    # ============================================================
    # 2D grafiklar: x(t) / v(t) / a(t)
    #   Vertical bo‘lsa: x~(t) ni ko‘rsatamiz (muvozanatga nisbatan)
    # ============================================================
    x_label = "x~ (m)" if mode == "vertical" else "x (m)"
    x_to_plot = x_tilde if mode == "vertical" else x

    fig1 = plt.figure(figsize=(6, 3))
    ax1 = fig1.add_subplot(111)
    ax1.plot(t, x_to_plot)
    ax1.set_xlabel("t (s)")
    ax1.set_ylabel(x_label)
    ax1.set_title("Siljish: " + ("x~(t) (muvozanatga nisbatan)" if mode == "vertical" else "x(t)"))
    ax1.grid(True, alpha=0.3)
    plot_x_base64 = _plot_to_base64(fig1)

    fig2 = plt.figure(figsize=(6, 3))
    ax2 = fig2.add_subplot(111)
    ax2.plot(t, v)
    ax2.set_xlabel("t (s)")
    ax2.set_ylabel("v (m/s)")
    ax2.set_title("Tezlik: v(t)")
    ax2.grid(True, alpha=0.3)
    plot_v_base64 = _plot_to_base64(fig2)

    fig3 = plt.figure(figsize=(6, 3))
    ax3 = fig3.add_subplot(111)
    ax3.plot(t, a)
    ax3.set_xlabel("t (s)")
    ax3.set_ylabel("a (m/s²)")
    ax3.set_title("Tezlanish: a(t)")
    ax3.grid(True, alpha=0.3)
    plot_a_base64 = _plot_to_base64(fig3)

    # ============================================================
    # Plotly 3D: fazoviy trayektoriya (x~, v, t)
    # ============================================================
    plotly_payload = {
        "data": [
            {
                "type": "scatter3d",
                "mode": "lines",
                "x": x_tilde.tolist(),   # x~ doim muvozanatga nisbatan
                "y": v.tolist(),
                "z": t.tolist(),
                "line": {"width": 4},
            }
        ],
        "layout": {
            "title": "3D Fazoviy trayektoriya: (x~, v, t)",
            "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
            "scene": {
                "xaxis": {"title": "x~ (m)"},
                "yaxis": {"title": "v (m/s)"},
                "zaxis": {"title": "t (s)"},
            },
        },
    }

    # ============================================================
    # Statistika + ilmiy xulosa
    # ============================================================
    stats = {
        "omega0": f"{omega0:.6g}",
        "zeta": f"{zeta:.6g}",
        "regime": regime,
        "x_eq": (f"{x_eq:.6g}" if mode == "vertical" else None),

        "x_max": float(np.max(x_to_plot)),
        "x_min": float(np.min(x_to_plot)),
        "v_max": float(np.max(v)),
        "v_min": float(np.min(v)),
    }

    conclusion = _build_conclusion_osc2(
        mode=mode, g=g,
        m=m, k=k, c=c,
        x0=x0, v0=v0,
        x_eq=x_eq,
        omega0=omega0, zeta=zeta, regime=regime,
        tmax=tmax
    )

    # ============================================================
    # MUHIM: form=data (DICT) — template input value lar to‘g‘ri chiqadi
    # ============================================================
    context = {
        "page_title": "Mass–Spring 2 | DiffPhys",
        "form": data,
        "plot_x_base64": plot_x_base64,
        "plot_v_base64": plot_v_base64,
        "plot_a_base64": plot_a_base64,
        "plotly_payload": json.dumps(plotly_payload),
        "stats": stats,
        "conclusion": conclusion,
        "scipy_ok": SCIPY_OK,
    }
    return render(request, "ai_module/mass_spring2.html", context)


# ============================================================
# Xulosa builder (mass_spring2 uchun alohida)
# ============================================================
def _build_conclusion_osc2(
    mode: str, g: float,
    m: float, k: float, c: float,
    x0: float, v0: float,
    x_eq: float,
    omega0: float, zeta: float, regime: str,
    tmax: float
) -> str:
    if mode == "vertical":
        extra = f"Vertikal holatda muvozanat siljishi x_eq = m·g/k = {x_eq:.4g} m; tahlil x~ = x - x_eq bo‘yicha bajarildi."
    else:
        extra = "Gorizontal holatda (oddiy Hooke modeli) x_eq = 0 deb olinadi."

    return (
        f"Berilgan tizim m x'' + c x' + k x = 0 (muvozanatga nisbatan) ko‘rinishida yechildi. "
        f"Tabiiy chastota ω0 = √(k/m) = {omega0:.4g} rad/s. "
        f"So‘nish koeffitsiyenti bo‘yicha damping ratio ζ = c/(2√(mk)) = {zeta:.4g}, rejim: {regime}. "
        f"Boshlang‘ich shartlar: x(0)={x0:.4g} m, v(0)={v0:.4g} m/s; hisoblash oraliği t∈[0, {tmax:.4g}] s. "
        f"{extra}"
    )


# ============================================================
# PDF: Mass-Spring2 (grafiklar bilan)
# ============================================================
def mass_spring2_pdf(request):
    """
    POST orqali form qiymatlari keladi.
    PDF ichiga: parametrlar + ω0, ζ, regime + 3 ta grafik (x,v,a)
    """
    import json

    # POST dan olish
    try:
        mode = str(request.POST.get("mode", "horizontal")).strip().lower()
        if mode not in ("horizontal", "vertical"):
            mode = "horizontal"
    except Exception:
        mode = "horizontal"

    def _pf(key, default=0.0):
        try:
            return float(request.POST.get(key, default))
        except Exception:
            return float(default)

    def _pi(key, default=300):
        try:
            return int(request.POST.get(key, default))
        except Exception:
            return int(default)

    g = max(0.0, _pf("g", 9.81))
    m = max(1e-9, _pf("m", 1.0))
    k = max(1e-9, _pf("k", 20.0))
    c = max(0.0, _pf("c", 0.0))
    x0 = _pf("x0", 0.15)
    v0 = _pf("v0", 0.0)
    tmax = max(0.05, _pf("tmax", 10.0))
    nt = max(50, _pi("nt", 600))

    omega0 = float(np.sqrt(k / m))
    zeta = float(c / (2.0 * np.sqrt(m * k))) if (m > 0 and k > 0) else 0.0
    if c == 0.0:
        regime = "undamped"
    else:
        if zeta < 1.0:
            regime = "underdamped"
        elif abs(zeta - 1.0) < 1e-6:
            regime = "critical"
        else:
            regime = "overdamped"

    x_eq = float(m * g / k) if (mode == "vertical") else 0.0
    x_tilde0 = float(x0 - x_eq)

    def rhs(t, y):
        xt, v = y
        return [v, -(c / m) * v - (k / m) * xt]

    t_eval = np.linspace(0.0, tmax, nt)

    if SCIPY_OK and solve_ivp is not None:
        sol = solve_ivp(rhs, (0.0, tmax), [x_tilde0, v0], t_eval=t_eval, rtol=1e-7, atol=1e-9)
        t = sol.t
        x_tilde = sol.y[0]
        v = sol.y[1]
    else:
        t = t_eval
        dt = float(t[1] - t[0])
        x_tilde = np.zeros_like(t, dtype=float)
        v = np.zeros_like(t, dtype=float)
        x_tilde[0] = x_tilde0
        v[0] = v0
        for i in range(len(t) - 1):
            y = np.array([x_tilde[i], v[i]], dtype=float)
            k1 = np.array(rhs(t[i], y))
            k2 = np.array(rhs(t[i] + dt / 2, y + dt * k1 / 2))
            k3 = np.array(rhs(t[i] + dt / 2, y + dt * k2 / 2))
            k4 = np.array(rhs(t[i] + dt, y + dt * k3))
            y_next = y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            x_tilde[i + 1] = y_next[0]
            v[i + 1] = y_next[1]

    a = -(c / m) * v - (k / m) * x_tilde

    x_label = "x~ (m)" if mode == "vertical" else "x (m)"
    x_to_plot = x_tilde if mode == "vertical" else (x_tilde + x_eq)

    # Matplotlib fig -> bytes (PDF uchun)
    def _fig_bytes(fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
        plt.close(fig)
        return buf.getvalue()

    fig1 = plt.figure(figsize=(6.5, 3.2))
    ax1 = fig1.add_subplot(111)
    ax1.plot(t, x_to_plot)
    ax1.set_xlabel("t (s)")
    ax1.set_ylabel(x_label)
    ax1.set_title("Siljish")
    ax1.grid(True, alpha=0.3)
    img_x = _fig_bytes(fig1)

    fig2 = plt.figure(figsize=(6.5, 3.2))
    ax2 = fig2.add_subplot(111)
    ax2.plot(t, v)
    ax2.set_xlabel("t (s)")
    ax2.set_ylabel("v (m/s)")
    ax2.set_title("Tezlik")
    ax2.grid(True, alpha=0.3)
    img_v = _fig_bytes(fig2)

    fig3 = plt.figure(figsize=(6.5, 3.2))
    ax3 = fig3.add_subplot(111)
    ax3.plot(t, a)
    ax3.set_xlabel("t (s)")
    ax3.set_ylabel("a (m/s²)")
    ax3.set_title("Tezlanish")
    ax3.grid(True, alpha=0.3)
    img_a = _fig_bytes(fig3)

    # PDF (ReportLab) — rasm + matn
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="mass_spring2_report.pdf"'

    cpdf = canvas.Canvas(response, pagesize=A4)
    W, H = A4

    y = H - 50
    cpdf.setFont("Helvetica-Bold", 14)
    cpdf.drawString(40, y, "Mass–Spring 2 (damped/undamped) — Hisobot")
    y -= 22

    cpdf.setFont("Helvetica", 11)
    cpdf.drawString(40, y, f"Rejim: {mode}    m={m:.4g} kg    k={k:.4g} N/m    c={c:.4g} N·s/m    g={g:.4g} m/s²")
    y -= 16
    cpdf.drawString(40, y, f"x0={x0:.4g} m    v0={v0:.4g} m/s    tmax={tmax:.4g} s    nt={nt}")
    y -= 18

    cpdf.setFont("Helvetica", 11)
    cpdf.drawString(40, y, f"ω0={omega0:.4g} rad/s    ζ={zeta:.4g}    rejim={regime}")
    y -= 18

    if mode == "vertical":
        cpdf.drawString(40, y, f"x_eq = m·g/k = {x_eq:.4g} m (muvozanat siljishi), tahlil x~=x-x_eq bo‘yicha")
        y -= 18

    # rasmlar
    def _draw_img(img_bytes, title):
        nonlocal y
        if y < 330:
            cpdf.showPage()
            y = H - 50
        cpdf.setFont("Helvetica-Bold", 12)
        cpdf.drawString(40, y, title)
        y -= 10
        img = ImageReader(BytesIO(img_bytes))
        cpdf.drawImage(img, 40, y - 260, width=520, height=260, preserveAspectRatio=True, mask='auto')
        y -= 285

    _draw_img(img_x, "1) Siljish grafigi")
    _draw_img(img_v, "2) Tezlik grafigi")
    _draw_img(img_a, "3) Tezlanish grafigi")

    cpdf.showPage()
    cpdf.save()
    return response

import io
import math
import base64
import numpy as np

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import now

# ---- Matplotlib (PNG/base64) ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- ODE solver ----
try:
    from scipy.integrate import solve_ivp
except ImportError:
    solve_ivp = None

# ---- Plotly (3D) ----
from plotly.offline import plot
import plotly.graph_objects as go

# ---- PDF (ReportLab) ----
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


# ============================================================
# Helpers
# ============================================================

def _fget(request, key, default):
    """GET dan qiymat oladi, bo'sh bo'lsa default."""
    v = request.GET.get(key, None)
    if v is None or str(v).strip() == "":
        return default
    return v

def _to_float(x, default):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return default

def _to_int(x, default):
    try:
        return int(float(str(x).replace(",", ".")))
    except Exception:
        return default

def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _make_v_func(v_type: str, V0: float, freq: float):
    """
    V(t) turlari:
    - step  : V(t)=V0
    - sinus : V(t)=V0*sin(2*pi*f*t)
    """
    v_type = (v_type or "step").lower().strip()
    if v_type == "sinus":
        w = 2.0 * math.pi * max(freq, 1e-9)
        return lambda t: V0 * math.sin(w * t)
    return lambda t: V0

def _linspace_safe(tmax, n):
    n = max(int(n), 10)
    tmax = max(float(tmax), 1e-6)
    return np.linspace(0.0, tmax, n)

def _nice_conclusion_rc(R, C, V0, v_type):
    tau = R * C
    if v_type == "step":
        return f"RC zanjiri uchun vaqt doimiysi τ = R·C = {tau:.6g} s. Step kuchlanishda tizim eksponensial rejimda zaryadlanadi/razryadlanadi."
    return f"RC zanjiri uchun τ = R·C = {tau:.6g} s. Sinus kuchlanishda q(t), i(t), Vc(t) faza siljishi bilan periodik o'zgaradi."

def _nice_conclusion_rl(R, L, V0, v_type):
    tau = L / max(R, 1e-12)
    if v_type == "step":
        return f"RL zanjiri uchun vaqt doimiysi τ = L/R = {tau:.6g} s. Step kuchlanishda tok i(t) eksponensial o'sadi/so'nadi."
    return f"RL zanjiri uchun τ = L/R = {tau:.6g} s. Sinus kuchlanishda i(t) va di/dt periodik rejimda bo'ladi."

def _pdf_header(c, title):
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, 28.2*cm, title)
    c.setFont("Helvetica", 9)
    c.drawRightString(19.8*cm, 28.2*cm, now().strftime("%d/%m/%Y %H:%M"))

def _pdf_params_block(c, params: list, x=2*cm, y=27.2*cm):
    """
    params: [(name, value_str), ...]
    """
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Parametrlar:")
    c.setFont("Helvetica", 10)
    yy = y - 0.6*cm
    for k, v in params:
        c.drawString(x, yy, f"- {k}: {v}")
        yy -= 0.48*cm
    return yy

def _pdf_conclusion(c, text, x=2*cm, y=2.2*cm):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y + 0.55*cm, "Xulosa:")
    c.setFont("Helvetica", 10)
    # simple wrap
    max_chars = 110
    lines = []
    s = text.strip()
    while len(s) > max_chars:
        cut = s.rfind(" ", 0, max_chars)
        if cut <= 0:
            cut = max_chars
        lines.append(s[:cut].strip())
        s = s[cut:].strip()
    if s:
        lines.append(s)
    yy = y
    for ln in lines[:5]:
        c.drawString(x, yy, ln)
        yy -= 0.45*cm

def _pdf_page_number(c, page_no):
    c.setFont("Helvetica", 9)
    c.drawRightString(19.8*cm, 1.2*cm, f"{page_no}")


# ============================================================
# 1) RC Circuit: dq/dt + (1/RC) q = V(t)/R
#     q(t), i(t)=dq/dt, Vc(t)=q/C
# ============================================================

def _simulate_rc(R, C, q0, tmax, nt, v_type, V0, freq):
    R = max(R, 1e-12)
    C = max(C, 1e-12)

    V = _make_v_func(v_type, V0, freq)
    t_eval = _linspace_safe(tmax, nt)

    # dq/dt = V(t)/R - (1/(R*C))*q
    def f(t, q):
        return (V(t) / R) - (q / (R * C))

    sol = solve_ivp(
        fun=lambda t, y: [f(t, y[0])],
        t_span=(0.0, float(tmax)),
        y0=[float(q0)],
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-9
    )

    t = sol.t
    q = sol.y[0]
    # i(t) = dq/dt (analitikdan emas, numerik differensial)
    i = np.gradient(q, t)
    Vc = q / C
    Vt = np.array([V(tt) for tt in t])
    return t, q, i, Vc, Vt

def _plots_rc(t, q, i, Vc):
    # q(t)
    fig1 = plt.figure()
    plt.plot(t, q)
    plt.xlabel("t (s)")
    plt.ylabel("q(t) (C)")
    plt.title("RC: Zaryad q(t)")
    q_png = _fig_to_base64(fig1)

    # i(t)
    fig2 = plt.figure()
    plt.plot(t, i)
    plt.xlabel("t (s)")
    plt.ylabel("i(t) (A)")
    plt.title("RC: Tok i(t)=dq/dt")
    i_png = _fig_to_base64(fig2)

    # Vc(t)
    fig3 = plt.figure()
    plt.plot(t, Vc)
    plt.xlabel("t (s)")
    plt.ylabel("Vc(t) (V)")
    plt.title("RC: Kondensator kuchlanishi Vc(t)=q/C")
    vc_png = _fig_to_base64(fig3)

    return q_png, i_png, vc_png

def _plotly_3d_rc(R, C, q0, tmax, nt, v_type, V0, freq):
    """
    3D: t - C - q(t) (y o'qi: C sweep)
    """
    t_grid = _linspace_safe(tmax, min(nt, 70))
    # C ni +/-50% diapazonda sweep
    Cmin = max(C * 0.5, 1e-12)
    Cmax = C * 1.5
    Cs = np.linspace(Cmin, Cmax, 30)

    Z = []
    for Ci in Cs:
        t, q, _, _, _ = _simulate_rc(R, float(Ci), q0, tmax, len(t_grid), v_type, V0, freq)
        Z.append(q)
    Z = np.array(Z)  # shape (len(Cs), len(t))

    fig = go.Figure(data=[go.Surface(x=t_grid, y=Cs, z=Z)])
    fig.update_layout(
        title="RC 3D: q(t) sirt (t - C - q)",
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="C (F)",
            zaxis_title="q (C)"
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520
    )
    return plot(fig, output_type="div", include_plotlyjs=False)


# ============================================================
# 2) RL Circuit: di/dt + (R/L) i = V(t)/L
#     i(t), di/dt, (optional) VL = L di/dt
# ============================================================

def _simulate_rl(R, L, i0, tmax, nt, v_type, V0, freq):
    R = max(R, 1e-12)
    L = max(L, 1e-12)

    V = _make_v_func(v_type, V0, freq)
    t_eval = _linspace_safe(tmax, nt)

    # di/dt = V(t)/L - (R/L)*i
    def f(t, i):
        return (V(t) / L) - (R / L) * i

    sol = solve_ivp(
        fun=lambda t, y: [f(t, y[0])],
        t_span=(0.0, float(tmax)),
        y0=[float(i0)],
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-9
    )

    t = sol.t
    i = sol.y[0]
    didt = np.gradient(i, t)
    Vl = L * didt
    Vt = np.array([V(tt) for tt in t])
    return t, i, didt, Vl, Vt

def _plots_rl(t, i, didt, Vl):
    # i(t)
    fig1 = plt.figure()
    plt.plot(t, i)
    plt.xlabel("t (s)")
    plt.ylabel("i(t) (A)")
    plt.title("RL: Tok i(t)")
    i_png = _fig_to_base64(fig1)

    # di/dt
    fig2 = plt.figure()
    plt.plot(t, didt)
    plt.xlabel("t (s)")
    plt.ylabel("di/dt (A/s)")
    plt.title("RL: Hosila di/dt")
    didt_png = _fig_to_base64(fig2)

    # VL(t)
    fig3 = plt.figure()
    plt.plot(t, Vl)
    plt.xlabel("t (s)")
    plt.ylabel("V_L(t) (V)")
    plt.title("RL: Induktorda kuchlanish V_L(t)=L·di/dt")
    vl_png = _fig_to_base64(fig3)

    return i_png, didt_png, vl_png

def _plotly_3d_rl(R, L, i0, tmax, nt, v_type, V0, freq):
    """
    3D: t - R - i(t) (y o'qi: R sweep)
    """
    t_grid = _linspace_safe(tmax, min(nt, 70))
    # R ni +/-50% diapazonda sweep
    Rmin = max(R * 0.5, 1e-12)
    Rmax = R * 1.5
    Rs = np.linspace(Rmin, Rmax, 30)

    Z = []
    for Ri in Rs:
        t, i, _, _, _ = _simulate_rl(float(Ri), L, i0, tmax, len(t_grid), v_type, V0, freq)
        Z.append(i)
    Z = np.array(Z)

    fig = go.Figure(data=[go.Surface(x=t_grid, y=Rs, z=Z)])
    fig.update_layout(
        title="RL 3D: i(t) sirt (t - R - i)",
        scene=dict(
            xaxis_title="t (s)",
            yaxis_title="R (Ohm)",
            zaxis_title="i (A)"
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520
    )
    return plot(fig, output_type="div", include_plotlyjs=False)


# ============================================================
# UI Views
# ============================================================

def rc_circuit_view(request):
    defaults = {
        "R": 10.0,
        "C": 0.01,
        "q0": 0.0,
        "tmax": 5.0,
        "nt": 400,
        "v_type": "step",  # step | sinus
        "V0": 5.0,
        "freq": 1.0,       # Hz (sinus uchun)
    }

    R = _to_float(_fget(request, "R", defaults["R"]), defaults["R"])
    C = _to_float(_fget(request, "C", defaults["C"]), defaults["C"])
    q0 = _to_float(_fget(request, "q0", defaults["q0"]), defaults["q0"])
    tmax = _to_float(_fget(request, "tmax", defaults["tmax"]), defaults["tmax"])
    nt = _to_int(_fget(request, "nt", defaults["nt"]), defaults["nt"])
    v_type = str(_fget(request, "v_type", defaults["v_type"])).lower().strip()
    V0 = _to_float(_fget(request, "V0", defaults["V0"]), defaults["V0"])
    freq = _to_float(_fget(request, "freq", defaults["freq"]), defaults["freq"])

    t, q, i, Vc, Vt = _simulate_rc(R, C, q0, tmax, nt, v_type, V0, freq)
    q_png, i_png, vc_png = _plots_rc(t, q, i, Vc)

    plot3d_div = _plotly_3d_rc(R, C, q0, tmax, nt, v_type, V0, freq)

    ctx = {
        "title": "RC zanjiri (zaryadlanish/razryad) — 1-tartibli ODE (Koshi)",
        "params": {
            "R": R, "C": C, "q0": q0, "tmax": tmax, "nt": nt,
            "v_type": v_type, "V0": V0, "freq": freq
        },
        "q_png": q_png,
        "i_png": i_png,
        "vc_png": vc_png,
        "plot3d_div": plot3d_div,
        "conclusion": _nice_conclusion_rc(R, C, V0, v_type),
    }
    return render(request, "ai_module/rc_circuit.html", ctx)


def rl_circuit_view(request):
    defaults = {
        "R": 10.0,
        "L": 0.5,
        "i0": 0.0,
        "tmax": 5.0,
        "nt": 400,
        "v_type": "step",  # step | sinus
        "V0": 5.0,
        "freq": 1.0,       # Hz (sinus uchun)
    }

    R = _to_float(_fget(request, "R", defaults["R"]), defaults["R"])
    L = _to_float(_fget(request, "L", defaults["L"]), defaults["L"])
    i0 = _to_float(_fget(request, "i0", defaults["i0"]), defaults["i0"])
    tmax = _to_float(_fget(request, "tmax", defaults["tmax"]), defaults["tmax"])
    nt = _to_int(_fget(request, "nt", defaults["nt"]), defaults["nt"])
    v_type = str(_fget(request, "v_type", defaults["v_type"])).lower().strip()
    V0 = _to_float(_fget(request, "V0", defaults["V0"]), defaults["V0"])
    freq = _to_float(_fget(request, "freq", defaults["freq"]), defaults["freq"])

    t, i, didt, Vl, Vt = _simulate_rl(R, L, i0, tmax, nt, v_type, V0, freq)
    i_png, didt_png, vl_png = _plots_rl(t, i, didt, Vl)

    plot3d_div = _plotly_3d_rl(R, L, i0, tmax, nt, v_type, V0, freq)

    ctx = {
        "title": "RL zanjiri (tokning o‘sishi/so‘nishi) — 1-tartibli ODE (Koshi)",
        "params": {
            "R": R, "L": L, "i0": i0, "tmax": tmax, "nt": nt,
            "v_type": v_type, "V0": V0, "freq": freq
        },
        "i_png": i_png,
        "didt_png": didt_png,
        "vl_png": vl_png,
        "plot3d_div": plot3d_div,
        "conclusion": _nice_conclusion_rl(R, L, V0, v_type),
    }
    return render(request, "ai_module/rl_circuit.html", ctx)


# ============================================================
# PDF Views
# - 3 grafik + parametrlar + xulosa
# ============================================================

def rc_circuit_pdf_view(request):
    # params (UI bilan bir xil)
    R = _to_float(_fget(request, "R", 10.0), 10.0)
    C = _to_float(_fget(request, "C", 0.01), 0.01)
    q0 = _to_float(_fget(request, "q0", 0.0), 0.0)
    tmax = _to_float(_fget(request, "tmax", 5.0), 5.0)
    nt = _to_int(_fget(request, "nt", 400), 400)
    v_type = str(_fget(request, "v_type", "step")).lower().strip()
    V0 = _to_float(_fget(request, "V0", 5.0), 5.0)
    freq = _to_float(_fget(request, "freq", 1.0), 1.0)

    t, q, i, Vc, _ = _simulate_rc(R, C, q0, tmax, nt, v_type, V0, freq)

    # 3 grafikni PDF uchun rasmga tayyorlaymiz
    imgs = []
    titles = [
        ("RC: q(t)", t, q, "t (s)", "q(t) (C)"),
        ("RC: i(t)=dq/dt", t, i, "t (s)", "i(t) (A)"),
        ("RC: Vc(t)=q/C", t, Vc, "t (s)", "Vc(t) (V)"),
    ]
    for ttl, xx, yy, xl, yl in titles:
        fig = plt.figure()
        plt.plot(xx, yy)
        plt.xlabel(xl)
        plt.ylabel(yl)
        plt.title(ttl)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    # PDF
    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)

    _pdf_header(cpdf, "RC zanjiri — PDF hisobot")
    y_after = _pdf_params_block(cpdf, [
        ("R (Ohm)", f"{R:g}"),
        ("C (F)", f"{C:g}"),
        ("Boshlang'ich q0 (C)", f"{q0:g}"),
        ("tmax (s)", f"{tmax:g}"),
        ("Nuqtalar soni nt", f"{nt:d}"),
        ("V(t) turi", f"{v_type}"),
        ("V0 (V)", f"{V0:g}"),
        ("freq (Hz, sinus uchun)", f"{freq:g}"),
    ], y=27.2*cm)

    # Grafiklar joylashuvi
    # 3 ta rasmni vertikal joylaymiz
    x0 = 2*cm
    w = 17.0*cm
    h = 6.0*cm
    y_top = 22.0*cm

    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h + 0.7*cm)
        cpdf.drawImage(ImageReader(img_buf), x0, y - h, width=w, height=h, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, _nice_conclusion_rc(R, C, V0, v_type), x=2*cm, y=2.2*cm)
    _pdf_page_number(cpdf, 1)

    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="rc_circuit_report.pdf"'
    return resp


def rl_circuit_pdf_view(request):
    # params (UI bilan bir xil)
    R = _to_float(_fget(request, "R", 10.0), 10.0)
    L = _to_float(_fget(request, "L", 0.5), 0.5)
    i0 = _to_float(_fget(request, "i0", 0.0), 0.0)
    tmax = _to_float(_fget(request, "tmax", 5.0), 5.0)
    nt = _to_int(_fget(request, "nt", 400), 400)
    v_type = str(_fget(request, "v_type", "step")).lower().strip()
    V0 = _to_float(_fget(request, "V0", 5.0), 5.0)
    freq = _to_float(_fget(request, "freq", 1.0), 1.0)

    t, i, didt, Vl, _ = _simulate_rl(R, L, i0, tmax, nt, v_type, V0, freq)

    imgs = []
    titles = [
        ("RL: i(t)", t, i, "t (s)", "i(t) (A)"),
        ("RL: di/dt", t, didt, "t (s)", "di/dt (A/s)"),
        ("RL: V_L(t)=L·di/dt", t, Vl, "t (s)", "V_L(t) (V)"),
    ]
    for ttl, xx, yy, xl, yl in titles:
        fig = plt.figure()
        plt.plot(xx, yy)
        plt.xlabel(xl)
        plt.ylabel(yl)
        plt.title(ttl)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        imgs.append(buf)

    out = io.BytesIO()
    cpdf = canvas.Canvas(out, pagesize=A4)

    _pdf_header(cpdf, "RL zanjiri — PDF hisobot")
    y_after = _pdf_params_block(cpdf, [
        ("R (Ohm)", f"{R:g}"),
        ("L (H)", f"{L:g}"),
        ("Boshlang'ich i0 (A)", f"{i0:g}"),
        ("tmax (s)", f"{tmax:g}"),
        ("Nuqtalar soni nt", f"{nt:d}"),
        ("V(t) turi", f"{v_type}"),
        ("V0 (V)", f"{V0:g}"),
        ("freq (Hz, sinus uchun)", f"{freq:g}"),
    ], y=27.2*cm)

    x0 = 2*cm
    w = 17.0*cm
    h = 6.0*cm
    y_top = 22.0*cm

    for idx, img_buf in enumerate(imgs):
        y = y_top - idx*(h + 0.7*cm)
        cpdf.drawImage(ImageReader(img_buf), x0, y - h, width=w, height=h, preserveAspectRatio=True, anchor='c')

    _pdf_conclusion(cpdf, _nice_conclusion_rl(R, L, V0, v_type), x=2*cm, y=2.2*cm)
    _pdf_page_number(cpdf, 1)

    cpdf.showPage()
    cpdf.save()

    out.seek(0)
    resp = HttpResponse(out.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="rl_circuit_report.pdf"'
    return resp

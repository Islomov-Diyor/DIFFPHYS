# core/views.py
from __future__ import annotations

import json
from pathlib import Path

import requests
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from docs.models import (
    Lecture,
    PedagogikTexnologiya,
    BaholashMezoni,
    MaslahatTavsiyalar,
    MashgulotIshlanmalari,
    MeyoriyHujjat,
)


# =========================
# 1) BOSH SAHIFA / STATIK SAHIFALAR
# =========================
def home(request):
    cards = [
        ("bi-graph-up", "Differensial tenglamalar",
         "Oddiy va xususiy hosilali differensial tenglamalar asoslari va yechim usullari."),
        ("bi-cpu", "Fizik modellashtirish",
         "Issiqlik, tebranish va elektr jarayonlarini matematik modellar asosida tahlil qilish."),
        ("bi-play-circle", "Videodarslar",
         "Differensial tenglamalar asosida fizik jarayonlarni tushuntiruvchi videodarslar."),
        ("bi-sliders", "Amaliy mashg‘ulotlar",
         "Amaliy masalalar, laboratoriya ishlari va real fizik jarayonlar tahlili."),
        ("bi-ui-checks", "Testlar",
         "Nazorat savollari va interaktiv testlar orqali bilimlarni baholash."),
        ("bi-file-earmark-text", "Taqdimotlar",
         "Mavzular bo‘yicha tayyor prezentatsiyalar va metodik materiallar."),
    ]

    links = [
        ("images/physics.png", "Fizika bo‘yicha onlayn portal", "physics.org", "https://www.physics.org"),
        ("images/khan.png", "Differensial tenglamalar (Khan Academy)", "khanacademy.org",
         "https://www.khanacademy.org/math/differential-equations"),
        ("images/mit.png", "MIT OpenCourseWare – Fizika kurslari", "ocw.mit.edu", "https://ocw.mit.edu"),
        ("images/wolfram.png", "Wolfram namoyishlari (modellar)", "demonstrations.wolfram.com",
         "https://demonstrations.wolfram.com"),
        ("images/scipy.png", "SciPy – differensial tenglamalar kutubxonasi", "scipy.org", "https://scipy.org"),
    ]
    return render(request, "core/home.html", {"cards": cards, "links": links})


def is_stu(request):
    return render(request, "core/is_stu.html")


def is_tech(request):
    return render(request, "core/is_tech.html")


# =========================
# 2) CONTACT
# =========================
def contact_view(request):
    """
    Eslatma: token/chat_id ni idealda .env orqali yashirish kerak.
    """
    success = False
    if request.method == "POST":
        name = request.POST.get("name", "")
        telegram = request.POST.get("telegram", "")
        message = request.POST.get("message", "")

        token = "8309490232:AAF_Qa-csaRznN7KhMK6IqMy-and9EWZ3go"
        chat_id = "6202834978"

        text = f"Yangi xabar:\n👤 Ismi: {name}\n📨 Telegram: {telegram}\n📝 Xabar: {message}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": text}

        try:
            r = requests.post(url, data=data, timeout=15)
            success = (r.status_code == 200)
        except requests.RequestException:
            success = False

    return render(request, "core/contact.html", {"success": success})


# =========================
# 3) MA'RUZALAR (CARD'LAR)
# =========================
def lecture_list(request):
    """
    Template: core/maruzalar.html
    Context: documents = lectures
    doc.has_pdf = pdf_file DBda bor + storage'da ham mavjud
    """
    lectures = list(Lecture.objects.all().order_by("lecture_number", "id"))
    for lec in lectures:
        try:
            lec.has_pdf = bool(lec.pdf_file) and lec.pdf_file.storage.exists(lec.pdf_file.name)
        except Exception:
            lec.has_pdf = False

    return render(request, "core/maruzalar.html", {"documents": lectures})


def download_document(request, pk: int):
    """
    PDF bo‘lmasa ham server yiqilmasin:
    - pdf_file yo‘q bo‘lsa -> 404
    - storage'da topilmasa -> 404
    """
    obj = get_object_or_404(Lecture, pk=pk)

    if not obj.pdf_file:
        raise Http404("PDF biriktirilmagan.")

    if not obj.pdf_file.storage.exists(obj.pdf_file.name):
        raise Http404("PDF fayl topilmadi. Admin paneldan PDFni qayta yuklang.")

    obj.download_count = (obj.download_count or 0) + 1
    obj.save(update_fields=["download_count"])

    return FileResponse(obj.pdf_file.open("rb"), as_attachment=True)


# =========================
# 4) TEST (JSON DAN)
# =========================
# core/views.py
import json
from pathlib import Path
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from docs.models import Lecture


def lecture_test(request, pk: int):
    lecture = get_object_or_404(Lecture, pk=pk)

    questions = []
    test_title = f"{lecture.lecture_number}-ma'ruza testi"

    quiz_file = (lecture.quiz_json or "").strip()

    if quiz_file:
        json_path = Path(settings.BASE_DIR) / "static" / "tests" / quiz_file

        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))

            # ===== SIZNING JSON FORMAT =====
            quiz = data.get("quiz", {})
            test_title = quiz.get("title", test_title)
            raw_questions = quiz.get("questions", [])

            for q in raw_questions:
                opts = q.get("options", {})

                keys = ["A", "B", "C", "D"]
                choices = [opts.get(k, "") for k in keys]

                correct_letter = q.get("correct_answer", "A")
                answer_index = keys.index(correct_letter) if correct_letter in keys else 0

                questions.append({
                    "question": q.get("question", ""),
                    "choices": choices,
                    "answer_index": answer_index,
                    "explanation": q.get("explanation", ""),
                })

    return render(request, "core/lecture_test.html", {
        "lecture": lecture,
        "test_title": test_title,
        "questions": questions,
    })



# =========================
# 5) METODIK TA'MINOT
# =========================
def metodik_taminot(request):
    context = {
        "ped_texnologiyalar": PedagogikTexnologiya.objects.all(),
        "baholash_mezonlari": BaholashMezoni.objects.all(),
        "maslahat_tavsiyalar": MaslahatTavsiyalar.objects.all(),
        "mashgulot_ishlanmalari": MashgulotIshlanmalari.objects.all(),
    }
    return render(request, "core/metodik_taminot.html", context)


def _safe_download_generic(obj, field_name: str, count_field: str = "yuklashlar_soni"):
    f = getattr(obj, field_name, None)
    if not f:
        raise Http404("Fayl biriktirilmagan.")
    if not f.storage.exists(f.name):
        raise Http404("Fayl topilmadi. Admin paneldan qayta yuklang.")

    current = getattr(obj, count_field, 0) or 0
    setattr(obj, count_field, current + 1)
    obj.save(update_fields=[count_field])

    return FileResponse(f.open("rb"), as_attachment=True)


def download_ped_texnologiya(request, pk: int):
    obj = get_object_or_404(PedagogikTexnologiya, pk=pk)
    return _safe_download_generic(obj, field_name="fayl", count_field="yuklashlar_soni")


def download_baholash_mezon(request, pk: int):
    obj = get_object_or_404(BaholashMezoni, pk=pk)
    return _safe_download_generic(obj, field_name="fayl", count_field="yuklashlar_soni")


def download_maslahat(request, pk: int):
    obj = get_object_or_404(MaslahatTavsiyalar, pk=pk)
    return _safe_download_generic(obj, field_name="fayl", count_field="yuklashlar_soni")


def download_mashgulot(request, pk: int):
    obj = get_object_or_404(MashgulotIshlanmalari, pk=pk)
    return _safe_download_generic(obj, field_name="fayl", count_field="yuklashlar_soni")


# =========================
# 6) ME'YORIY HUJJATLAR
# =========================
def meyoriy_hujjatlar(request):
    turkumlar = {}
    for tur, nom in MeyoriyHujjat.HUJJAT_TURLARI:
        turkumlar[nom] = MeyoriyHujjat.objects.filter(tur=tur)
    return render(request, "core/meyoriy_hujjatlar.html", {"turkumlar": turkumlar})


def download_hujjat(request, pk: int):
    obj = get_object_or_404(MeyoriyHujjat, pk=pk)
    return _safe_download_generic(obj, field_name="fayl", count_field="yuklashlar_soni")


# =========================
# 7) NAZORAT (agar core orqali ochsangiz)
# =========================
def nazorat_view(request):
    return render(request, "docs/nazorat.html")

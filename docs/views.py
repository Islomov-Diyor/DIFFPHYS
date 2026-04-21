from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from .models import Presentation, Practical, VideoLesson


def presentations_view(request):
    presentations = Presentation.objects.all().order_by("lecture_number")
    return render(request, "docs/presentations.html", {"presentations": presentations})


def download_presentation(request, pk):
    presentation = get_object_or_404(Presentation, pk=pk)

    # download_count None bo‘lsa ham ishlasin
    presentation.download_count = (presentation.download_count or 0) + 1
    presentation.save(update_fields=["download_count"])

    # FileResponse uchun faylni ochib beramiz
    f = presentation.file.open("rb")
    return FileResponse(f, as_attachment=True, filename=presentation.file.name.split("/")[-1])


def practicals_view(request):
    practicals = Practical.objects.all().order_by("upload_date")
    return render(request, "docs/practicals.html", {"practicals": practicals})


def download_practical(request, pk):
    practical = get_object_or_404(Practical, pk=pk)

    practical.download_count = (practical.download_count or 0) + 1
    practical.save(update_fields=["download_count"])

    f = practical.file.open("rb")
    return FileResponse(f, as_attachment=True, filename=practical.file.name.split("/")[-1])


def video_lessons(request):
    videos = VideoLesson.objects.all().order_by("lesson_number")
    return render(request, "docs/videos.html", {"videos": videos})


def nazorat_view(request):
    return render(request, "docs/nazorat.html")


try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Presentation

def presentation_thumb(request, pk):
    p = get_object_or_404(Presentation, pk=pk)

    if not p.file:
        return HttpResponse(status=404)

    # faqat PDF preview
    if not p.file.name.lower().endswith(".pdf"):
        return HttpResponse(status=404)

    doc = fitz.open(p.file.path)
    page = doc.load_page(0)  # 1-sahifa
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    doc.close()

    return HttpResponse(pix.tobytes("png"), content_type="image/png")

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Practical

def practical_thumb(request, pk):
    p = get_object_or_404(Practical, pk=pk)

    if not p.file:
        return HttpResponse(status=404)

    if not p.file.name.lower().endswith(".pdf"):
        return HttpResponse(status=404)

    doc = fitz.open(p.file.path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    doc.close()

    return HttpResponse(pix.tobytes("png"), content_type="image/png")
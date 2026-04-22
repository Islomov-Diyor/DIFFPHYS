from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Practical, Presentation, VideoLesson

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def _safe_file_response(file_field, as_attachment=True):
    if not file_field:
        raise Http404("Fayl biriktirilmagan.")
    if not file_field.storage.exists(file_field.name):
        raise Http404("Fayl topilmadi. Admin paneldan qayta yuklang.")
    return FileResponse(
        file_field.open("rb"),
        as_attachment=as_attachment,
        filename=file_field.name.split("/")[-1],
    )


def _render_pdf_thumb(file_field):
    if fitz is None:
        return HttpResponse(status=404)
    if not file_field or not file_field.name.lower().endswith(".pdf"):
        return HttpResponse(status=404)
    if not file_field.storage.exists(file_field.name):
        return HttpResponse(status=404)

    with file_field.open("rb") as fh:
        data = fh.read()
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        png_bytes = pix.tobytes("png")
    finally:
        doc.close()

    return HttpResponse(png_bytes, content_type="image/png")


def presentations_view(request):
    presentations = Presentation.objects.all().order_by("lecture_number")
    return render(request, "docs/presentations.html", {"presentations": presentations})


def download_presentation(request, pk):
    presentation = get_object_or_404(Presentation, pk=pk)
    presentation.download_count = (presentation.download_count or 0) + 1
    presentation.save(update_fields=["download_count"])
    return _safe_file_response(presentation.file)


def practicals_view(request):
    practicals = Practical.objects.all().order_by("upload_date")
    return render(request, "docs/practicals.html", {"practicals": practicals})


def download_practical(request, pk):
    practical = get_object_or_404(Practical, pk=pk)
    practical.download_count = (practical.download_count or 0) + 1
    practical.save(update_fields=["download_count"])
    return _safe_file_response(practical.file)


def video_lessons(request):
    videos = VideoLesson.objects.all().order_by("lesson_number")
    return render(request, "docs/videos.html", {"videos": videos})


def nazorat_view(request):
    return render(request, "docs/nazorat.html")


def presentation_thumb(request, pk):
    p = get_object_or_404(Presentation, pk=pk)
    return _render_pdf_thumb(p.file)


def practical_thumb(request, pk):
    p = get_object_or_404(Practical, pk=pk)
    return _render_pdf_thumb(p.file)

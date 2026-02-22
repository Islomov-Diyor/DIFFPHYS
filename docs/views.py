from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from .models import Presentation, Practical, VideoLesson

def presentations_view(request):
    presentations = Presentation.objects.all().order_by('lecture_number')
    return render(request, 'docs/presentations.html', {'presentations': presentations})

def download_presentation(request, pk):
    presentation = get_object_or_404(Presentation, pk=pk)
    presentation.download_count += 1
    presentation.save()
    return FileResponse(presentation.file, as_attachment=True)

def practicals_view(request):
    practicals = Practical.objects.all().order_by('upload_date')
    return render(request, 'docs/practicals.html', {'practicals': practicals})

def download_practical(request, pk):
    practical = get_object_or_404(Practical, pk=pk)
    practical.download_count += 1
    practical.save()
    return FileResponse(practical.file, as_attachment=True)

def video_lessons(request):
    videos = VideoLesson.objects.all().order_by('lesson_number')
    return render(request, 'docs/videos.html', {'videos': videos})

def nazorat_view(request):
    return render(request, 'docs/nazorat.html')

from django.contrib import admin
from .models import (
    PedagogikTexnologiya,
    BaholashMezoni,
    MaslahatTavsiyalar,
    MashgulotIshlanmalari,
    MeyoriyHujjat,
    Lecture,
    Presentation,
    Practical,
)

@admin.register(PedagogikTexnologiya)
class PedagogikTexnologiyaAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'fayl', 'yuklashlar_soni')


@admin.register(BaholashMezoni)
class BaholashMezoniAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'fayl', 'yuklashlar_soni')


@admin.register(MaslahatTavsiyalar)
class MaslahatTavsiyalarAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'fayl', 'yuklashlar_soni')


@admin.register(MashgulotIshlanmalari)
class MashgulotIshlanmalariAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'fayl', 'yuklashlar_soni')


@admin.register(MeyoriyHujjat)
class MeyoriyHujjatAdmin(admin.ModelAdmin):
    list_display = ('sarlavha', 'tur', 'fayl', 'yuklashlar_soni')


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "lecture_number", "download_count")


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'lecture_number', 'subject', 'download_count', 'upload_date')
    list_editable = ('lecture_number',)
    ordering = ('lecture_number',)


@admin.register(Practical)
class PracticalAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'download_count', 'upload_date')

#---Videolar---

from django.contrib import admin
from .models import VideoLesson

@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ('lesson_number', 'title', 'youtube_url')
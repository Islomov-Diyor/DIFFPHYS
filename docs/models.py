from django.db import models
from django.conf import settings
import os
import uuid


# =========================
# UPLOAD PATHS (MODULE-LEVEL)
# =========================
def upload_meyoriy(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"meyoriy_hujjatlar/{uuid.uuid4().hex}{ext}"


def upload_ped_tex(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"pedagogik_texnologiyalar/{uuid.uuid4().hex}{ext}"


def upload_baholash(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"baholash_mezonlari/{uuid.uuid4().hex}{ext}"


def upload_maslahat(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"maslahat_tavsiyalar/{uuid.uuid4().hex}{ext}"


def upload_mashgulot(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"mashgulot_ishlanmalari/{uuid.uuid4().hex}{ext}"


def upload_lecture_pdf(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"lectures/{uuid.uuid4().hex}{ext}"


def upload_lecture_image(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"lectures/images/{uuid.uuid4().hex}{ext}"


def upload_presentation_file(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"presentations/{uuid.uuid4().hex}{ext}"


def upload_presentation_image(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"presentations/images/{uuid.uuid4().hex}{ext}"


def upload_practical_file(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"practicals/{uuid.uuid4().hex}{ext}"


def upload_practical_image(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"practicals/images/{uuid.uuid4().hex}{ext}"


# =========================
# MODELS
# =========================
class MeyoriyHujjat(models.Model):
    HUJJAT_TURLARI = [
        ("qonun", "Qonunlar"),
        ("qaror", "Qarorlar"),
        ("farmon", "Farmonlar"),
        ("metodik", "O'quv-metodik ta'minot"),
    ]

    sarlavha = models.CharField(max_length=255)
    tur = models.CharField(max_length=20, choices=HUJJAT_TURLARI, default="qonun")

    fayl = models.FileField(upload_to=upload_meyoriy, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.sarlavha


class PedagogikTexnologiya(models.Model):
    sarlavha = models.CharField(max_length=255)
    fayl = models.FileField(upload_to=upload_ped_tex, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.sarlavha


class BaholashMezoni(models.Model):
    sarlavha = models.CharField(max_length=255)
    fayl = models.FileField(upload_to=upload_baholash, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.sarlavha


class MaslahatTavsiyalar(models.Model):
    sarlavha = models.CharField(max_length=255)
    fayl = models.FileField(upload_to=upload_maslahat, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.sarlavha


class MashgulotIshlanmalari(models.Model):
    sarlavha = models.CharField(max_length=255)
    fayl = models.FileField(upload_to=upload_mashgulot, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.sarlavha


class Lecture(models.Model):
    title = models.CharField(max_length=255, verbose_name="Mavzu nomi")
    subject = models.CharField(max_length=255, verbose_name="Fan nomi")
    lecture_number = models.PositiveIntegerField(verbose_name="Mashg‘ulot tartib raqami")

    pdf_file = models.FileField(
        upload_to=upload_lecture_pdf,
        blank=True, null=True,
        verbose_name="PDF fayl",
        max_length=500
    )
    image = models.ImageField(
        upload_to=upload_lecture_image,
        blank=True, null=True,
        verbose_name="Rasm",
        max_length=500
    )

    download_count = models.PositiveIntegerField(default=0, verbose_name="Yuklab olish soni")

    class Meta:
        ordering = ["lecture_number", "id"]

    def __str__(self):
        return f"{self.lecture_number}-Ma'ruza: {self.title}"

    @property
    def pdf_exists(self) -> bool:
        if not self.pdf_file:
            return False
        try:
            return self.pdf_file.storage.exists(self.pdf_file.name)
        except Exception:
            return False

    @property
    def pdf_abs_path(self) -> str:
        if not self.pdf_file:
            return ""
        try:
            return self.pdf_file.path
        except Exception:
            return os.path.join(str(settings.MEDIA_ROOT), self.pdf_file.name)


class Presentation(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)

    lecture_number = models.PositiveIntegerField(default=1, verbose_name="Mashg‘ulot raqami")
    download_count = models.PositiveIntegerField(default=0)

    file = models.FileField(upload_to=upload_presentation_file, max_length=500)
    image = models.ImageField(
        upload_to=upload_presentation_image,
        blank=True, null=True,
        max_length=500
    )

    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["lecture_number", "-upload_date", "id"]

    def __str__(self):
        return self.title


class Practical(models.Model):
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)

    lecture_number = models.PositiveIntegerField(default=1, verbose_name="Mashg‘ulot raqami")
    file = models.FileField(upload_to=upload_practical_file, max_length=500)

    image = models.ImageField(
        upload_to=upload_practical_image,
        blank=True, null=True,
        max_length=500
    )
    upload_date = models.DateTimeField(auto_now_add=True)

    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["lecture_number", "-upload_date", "id"]

    def __str__(self):
        return self.title


class VideoLesson(models.Model):
    title = models.CharField(max_length=255)
    lesson_number = models.PositiveIntegerField()
    youtube_url = models.URLField()

    class Meta:
        ordering = ["lesson_number", "id"]

    def __str__(self):
        return f"{self.lesson_number}-dars: {self.title}"

quiz_json = models.CharField(
    max_length=255,
    blank=True,
    null=True,
    help_text="Masalan: lecture_01.json"
)

class Lecture(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, null=True)
    lecture_number = models.PositiveIntegerField(default=1)
    pdf_file = models.FileField(upload_to="lectures/", blank=True, null=True)
    download_count = models.PositiveIntegerField(default=0)

    quiz_json = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.lecture_number}-ma'ruza: {self.title}"
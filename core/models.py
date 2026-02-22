from django.db import models
import os
import uuid


# =========================
# UPLOAD PATHS (MODULE-LEVEL)
# =========================
def lecture_pdf_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"lectures/{uuid.uuid4().hex}{ext}"


def presentation_file_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"presentations/{uuid.uuid4().hex}{ext}"


def presentation_image_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"presentation_images/{uuid.uuid4().hex}{ext}"


def metodik_file_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"metodik/{uuid.uuid4().hex}{ext}"


def meyoriy_file_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"meyoriy_hujjatlar/{uuid.uuid4().hex}{ext}"


# =========================
# MODELS
# =========================
class Presentation(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    file = models.FileField(upload_to=presentation_file_upload_to, max_length=500)
    image = models.ImageField(
        upload_to=presentation_image_upload_to,
        blank=True, null=True,
        max_length=500
    )

    download_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Lecture(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, default="")
    lecture_number = models.PositiveIntegerField(default=1)

    pdf_file = models.FileField(
        upload_to=lecture_pdf_upload_to,
        blank=True, null=True,
        max_length=500
    )
    download_count = models.PositiveIntegerField(default=0)

    quiz_json = models.CharField(
        max_length=255,
        blank=True,
        help_text="Masalan: topic_01.json (tests papkasida turadi)"
    )

    class Meta:
        ordering = ["lecture_number", "id"]

    def __str__(self):
        return f"{self.lecture_number}-ma'ruza: {self.title}"


class PedagogikTexnologiya(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    fayl = models.FileField(upload_to=metodik_file_upload_to, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class BaholashMezoni(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    fayl = models.FileField(upload_to=metodik_file_upload_to, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class MaslahatTavsiyalar(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    fayl = models.FileField(upload_to=metodik_file_upload_to, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class MashgulotIshlanmalari(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    fayl = models.FileField(upload_to=metodik_file_upload_to, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class MeyoriyHujjat(models.Model):
    HUJJAT_TURLARI = [
        ("qonun", "Qonunlar"),
        ("qaror", "Qarorlar"),
        ("farmon", "Farmonlar"),
        ("buyruq", "Buyruqlar"),
        ("nizom", "Nizomlar"),
        ("boshqa", "Boshqa hujjatlar"),
    ]

    title = models.CharField(max_length=255)
    tur = models.CharField(max_length=20, choices=HUJJAT_TURLARI, default="boshqa")

    fayl = models.FileField(upload_to=meyoriy_file_upload_to, max_length=500)
    yuklashlar_soni = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

# core/models.py
from django.db import models

class Lecture(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, null=True)
    lecture_number = models.PositiveIntegerField(default=1)
    pdf_file = models.FileField(upload_to="lectures/", blank=True, null=True)
    download_count = models.PositiveIntegerField(default=0)

    # ✅ JSON fayl nomi: lecture_01.json
    quiz_json = models.CharField(max_length=255, blank=True, null=True, help_text="Masalan: lecture_01.json")

    @property
    def has_pdf(self):
        return bool(self.pdf_file)

    def __str__(self):
        return f"{self.lecture_number}-ma'ruza: {self.title}"

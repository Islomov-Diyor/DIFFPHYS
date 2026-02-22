"""users views.

Hozircha minimal view (placeholder). Keyinroq real sahifalar shu yerda yoziladi.
"""

from django.http import HttpResponse


def index(request):
    return HttpResponse("users app ishlayapti ✅ (placeholder)")

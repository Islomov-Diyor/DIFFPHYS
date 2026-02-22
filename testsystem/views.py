"""testsystem views.

Hozircha minimal view (placeholder). Keyinroq real sahifalar shu yerda yoziladi.
"""

from django.http import HttpResponse


def index(request):
    return HttpResponse("testsystem app ishlayapti ✅ (placeholder)")

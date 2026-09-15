from django.http import JsonResponse

from .models import Visit
from .tasks import greet


def greeting(request):
    # Full celery roundtrip: web -> redis broker -> worker -> redis result
    # backend -> web. The tag is read inside the worker process.
    line = greet.delay().get(timeout=10)
    Visit.objects.create()
    return JsonResponse(
        {"greeting": line, "celery": "ok", "visits": Visit.objects.count()}
    )


def health(request):
    return JsonResponse({"ok": True})

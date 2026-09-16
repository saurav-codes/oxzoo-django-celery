from django.db.models import Count, Sum
from django.http import JsonResponse

from .models import Sample, Visit
from .tasks import greet


def greeting(request):
    # Full celery roundtrip: web -> redis broker -> worker -> redis result
    # backend -> web. The tag is read inside the worker process, and the
    # worker also reads the row count from Postgres, so the response proves
    # both processes see the same database.
    result = greet.delay().get(timeout=10)
    Visit.objects.create()
    return JsonResponse(
        {
            "greeting": result["line"],
            "celery": "ok",
            "visits": Visit.objects.count(),
            "worker_visits": result["worker_visits"],
        }
    )


def slow(request):
    # A real aggregate over the seeded Sample table: the endpoint the
    # cutover and long-migration scenarios put under load.
    aggregate = Sample.objects.aggregate(rows=Count("id"), total=Sum("value"))
    return JsonResponse({"rows": aggregate["rows"], "total": aggregate["total"] or 0})


def health(request):
    return JsonResponse({"ok": True})

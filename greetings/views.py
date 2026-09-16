from django.db.models import Count, Sum
from django.http import JsonResponse

from .models import Job, Sample, Visit
from .tasks import greet, long_job


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


def long_job_start(request):
    # Enqueue a task that outlives a deploy restart; the follow-up deploy is
    # what the worker-version-skew scenario interrupts.
    try:
        seconds = int(request.GET.get("seconds", "20"))
    except ValueError:
        return JsonResponse({"error": "seconds must be an integer"}, status=400)
    if seconds < 1 or seconds > 300:
        return JsonResponse({"error": "seconds must be between 1 and 300"}, status=400)
    result = long_job.delay(seconds=seconds)
    return JsonResponse({"task_id": result.id, "seconds": seconds})


def jobs(request):
    rows = [
        {
            "task_id": job.task_id,
            "seconds": job.seconds,
            "finished": job.finished,
            "started_at": job.started_at.isoformat(),
        }
        for job in Job.objects.order_by("-started_at")[:20]
    ]
    return JsonResponse({"jobs": rows})

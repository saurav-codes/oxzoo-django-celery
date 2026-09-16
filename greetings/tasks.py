import os

from celery import shared_task

APP_NAME = "oxzoo-django-celery"


def greeting_line() -> str:
    # Read inside the worker process at task time: GREETING_TAG is runtime env.
    return f"hello world {APP_NAME}_{os.environ.get('GREETING_TAG', 'unknown')}"


@shared_task
def greet():
    # The worker reads the counter from Postgres itself, so a database
    # restore has to be visible to a second process, not only to gunicorn.
    from .models import Visit

    return {"line": greeting_line(), "worker_visits": Visit.objects.count()}


@shared_task
def heartbeat():
    # print() lands in the worker journal; ox sets PYTHONUNBUFFERED=1 so the
    # line flushes on every beat tick.
    print(greeting_line())

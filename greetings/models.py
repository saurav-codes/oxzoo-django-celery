from django.db import models


class Visit(models.Model):
    # created_at was dropped by migration 0005 when DESTRUCTIVE_MIGRATION=drop
    # (the destructive-migration scenario). The model no longer writes it, so
    # a code rollback to a release that still does fails loudly instead of
    # silently serving stale data.
    pass


class Sample(models.Model):
    # Seeded by migration 0002 for the load, migration, and restore
    # scenarios: a real table large enough that a dump takes a moment and
    # an aggregate over it is measurable.
    label = models.CharField(max_length=64)
    value = models.IntegerField(default=0)


class Job(models.Model):
    # One row per long task, keyed by the Celery task id, so a redelivered
    # task after a deploy restart finishes exactly once.
    task_id = models.CharField(max_length=64, unique=True)
    seconds = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)

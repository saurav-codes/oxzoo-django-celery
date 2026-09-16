from django.db import models


class Visit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)


class Sample(models.Model):
    # Seeded by migration 0002 for the load, migration, and restore
    # scenarios: a real table large enough that a dump takes a moment and
    # an aggregate over it is measurable.
    label = models.CharField(max_length=64)
    value = models.IntegerField(default=0)

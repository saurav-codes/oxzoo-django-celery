# Job table for the worker-version-skew scenario: long_job writes one row
# keyed by the Celery task id, so a task interrupted by a deploy restart and
# redelivered finishes exactly once.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("greetings", "0002_sample_seed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_id", models.CharField(max_length=64, unique=True)),
                ("seconds", models.IntegerField(default=0)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished", models.BooleanField(default=False)),
            ],
        ),
    ]

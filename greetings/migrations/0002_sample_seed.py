# Seeded Sample table for the heavy scenarios: 0002 is a data migration, so
# a fresh deploy pays for 50k inserts once, a restore loads the dumped rows
# and skips the seed, and the table gives /api/slow/ something real to scan.

from django.db import migrations, models

SAMPLE_ROWS = 50_000
BATCH = 5_000


def seed_samples(apps, schema_editor):
    Sample = apps.get_model("greetings", "Sample")
    batch = []
    for i in range(SAMPLE_ROWS):
        batch.append(Sample(label=f"row-{i}", value=i))
        if len(batch) >= BATCH:
            Sample.objects.bulk_create(batch, batch_size=BATCH)
            batch.clear()
    if batch:
        Sample.objects.bulk_create(batch, batch_size=BATCH)


class Migration(migrations.Migration):

    dependencies = [
        ("greetings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(max_length=64)),
                ("value", models.IntegerField(default=0)),
            ],
        ),
        migrations.RunPython(seed_samples, migrations.RunPython.noop),
    ]

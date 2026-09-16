# Scenario fixture: hold an ACCESS EXCLUSIVE lock on the seeded table for
# MIGRATION_LOCK_SECONDS (default 0, a no-op) so a deploy's migrate hook can
# be measured against live read traffic. A production app avoids the lock
# (CREATE INDEX CONCURRENTLY, no table rewrite); this migration proves what a
# blocking DDL does to requests that keep arriving while it runs.

import os

from django.db import migrations


def lock_probe(apps, schema_editor):
    seconds = int(os.environ.get("MIGRATION_LOCK_SECONDS", "0") or "0")
    if seconds <= 0:
        return
    schema_editor.execute("LOCK TABLE greetings_sample IN ACCESS EXCLUSIVE MODE")
    schema_editor.execute(f"SELECT pg_sleep({seconds})")


class Migration(migrations.Migration):

    dependencies = [
        ("greetings", "0003_job"),
    ]

    operations = [
        migrations.RunPython(lock_probe, migrations.RunPython.noop),
    ]

# Scenario fixture: with DESTRUCTIVE_MIGRATION=drop, 0005 drops greetings_visit
# .created_at, a column the previous release still writes. Rolling the code
# back then fails loudly (the insert names a missing column) while the new
# release keeps working, which is what the rollback-warning check needs.
# Without the env var it is a no-op, so the migration is safe to leave in.

import os

from django.db import migrations


def drop_column(apps, schema_editor):
    if os.environ.get("DESTRUCTIVE_MIGRATION", "") != "drop":
        return
    schema_editor.execute("ALTER TABLE greetings_visit DROP COLUMN IF EXISTS created_at")


class Migration(migrations.Migration):

    dependencies = [
        ("greetings", "0004_lock_probe"),
    ]

    operations = [
        migrations.RunPython(drop_column, migrations.RunPython.noop),
    ]

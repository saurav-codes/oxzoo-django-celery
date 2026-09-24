# A fresh database never runs the destructive scenario (0005 is a no-op
# without DESTRUCTIVE_MIGRATION=drop), so greetings_visit.created_at stays
# NOT NULL with no default while the model no longer writes it — and
# Visit.objects.create() fails on every fresh deploy. Give the column a
# default when it exists; the scenario's drop still breaks the old release's
# explicit insert either way.

from django.db import migrations


def set_default(apps, schema_editor):
    schema_editor.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.columns
                     WHERE table_schema = 'public'
                       AND table_name = 'greetings_visit'
                       AND column_name = 'created_at') THEN
            ALTER TABLE greetings_visit ALTER COLUMN created_at SET DEFAULT now();
          END IF;
        END $$;
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ("greetings", "0005_destructive_probe"),
    ]

    operations = [
        migrations.RunPython(set_default, migrations.RunPython.noop),
    ]

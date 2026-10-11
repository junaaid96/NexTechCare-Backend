# Keep DB-level defaults so the legacy deployment (Render, old code) can still
# insert rows during the cut-over window. PostgreSQL only; no-op elsewhere.
from django.db import migrations

SQL = """
ALTER TABLE services_service ALTER COLUMN category SET DEFAULT 'software';
ALTER TABLE services_service ALTER COLUMN sla_hours SET DEFAULT 24;
ALTER TABLE services_service ALTER COLUMN is_remote SET DEFAULT true;
ALTER TABLE services_service ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE profiles_customerprofile ALTER COLUMN avatar_url SET DEFAULT '';
ALTER TABLE profiles_engineerprofile ALTER COLUMN avatar_url SET DEFAULT '';
ALTER TABLE profiles_adminprofile ALTER COLUMN avatar_url SET DEFAULT '';
ALTER TABLE profiles_engineerprofile ALTER COLUMN verified SET DEFAULT false;
"""


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(SQL)


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0002_alter_service_options_service_category_and_more'),
        ('profiles', '0003_adminprofile_avatar_url_customerprofile_avatar_url_and_more'),
    ]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

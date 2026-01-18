"""Enable pgvector extension (PostgreSQL only)."""

from django.db import migrations


def is_postgres(schema_editor):
    """Check if using PostgreSQL."""
    return schema_editor.connection.vendor == "postgresql"


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    "CREATE EXTENSION IF NOT EXISTS vector;",
                    [],
                ),
            ],
            reverse_sql=[
                (
                    "DROP EXTENSION IF EXISTS vector;",
                    [],
                ),
            ],
            # PostgreSQL에서만 실행
            state_operations=[],
        ),
    ]

    def apply(self, project_state, schema_editor, collect_sql=False):
        """PostgreSQL에서만 마이그레이션 적용."""
        if is_postgres(schema_editor):
            return super().apply(project_state, schema_editor, collect_sql)
        return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        """PostgreSQL에서만 마이그레이션 롤백."""
        if is_postgres(schema_editor):
            return super().unapply(project_state, schema_editor, collect_sql)
        return project_state

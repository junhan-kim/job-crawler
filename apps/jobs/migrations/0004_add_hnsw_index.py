"""embedding 필드에 HNSW 인덱스 추가 (벡터 검색 성능 최적화)."""

from django.db import migrations


def create_hnsw_index(apps, schema_editor):
    """PostgreSQL에서만 HNSW 인덱스 생성."""
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("""
        CREATE INDEX IF NOT EXISTS job_embedding_hnsw_idx
        ON jobs_jobposting
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def drop_hnsw_index(apps, schema_editor):
    """HNSW 인덱스 삭제."""
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("DROP INDEX IF EXISTS job_embedding_hnsw_idx;")


class Migration(migrations.Migration):
    """HNSW 인덱스 마이그레이션."""

    dependencies = [
        ("jobs", "0003_add_embedding"),
    ]

    operations = [
        migrations.RunPython(create_hnsw_index, drop_hnsw_index),
    ]

"""embedding 필드에 HNSW 인덱스 추가 (벡터 검색 성능 최적화)."""

from django.db import migrations


class Migration(migrations.Migration):
    """HNSW 인덱스 마이그레이션."""

    dependencies = [
        ("jobs", "0002_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS job_embedding_hnsw_idx
                ON jobs_jobposting
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """,
            reverse_sql="DROP INDEX IF EXISTS job_embedding_hnsw_idx;",
        ),
    ]

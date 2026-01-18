"""embedding 필드 추가."""

import pgvector.django.vector
from django.db import migrations


class Migration(migrations.Migration):
    """embedding 컬럼 추가 마이그레이션."""

    dependencies = [
        ("jobs", "0002_create_jobposting"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobposting",
            name="embedding",
            field=pgvector.django.vector.VectorField(
                blank=True, dimensions=768, null=True
            ),
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("actor_id", models.CharField(max_length=9)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("message", "Message"),
                            ("comment", "Comment"),
                            ("favorite", "Favorite"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True, null=True)),
                ("target_type", models.CharField(blank=True, max_length=32, null=True)),
                ("target_id", models.CharField(blank=True, max_length=64, null=True)),
                ("extra", models.JSONField(blank=True, null=True)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "is_read", "-created_at"], name="notificati_user_id_bbf8a0_idx"),
                    models.Index(fields=["type"], name="notificati_type_0e0d8c_idx"),
                ],
            },
        ),
    ]

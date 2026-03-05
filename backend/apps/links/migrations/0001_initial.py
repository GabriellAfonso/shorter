"""Initial migration — ShortURL and LinkClick models."""
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShortURL",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("original_url", models.URLField(max_length=2048, verbose_name="original URL")),
                ("slug", models.CharField(db_index=True, max_length=50, unique=True)),
                ("title", models.CharField(blank=True, max_length=200)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("click_count", models.PositiveIntegerField(default=0)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="short_urls",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Short URL",
                "verbose_name_plural": "Short URLs",
                "db_table": "short_urls",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="shorturl",
            index=models.Index(fields=["owner", "-created_at"], name="short_urls_owner_created_idx"),
        ),
        migrations.CreateModel(
            name="LinkClick",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("ip_address", models.CharField(blank=True, max_length=64)),
                ("user_agent", models.TextField(blank=True)),
                ("referrer", models.URLField(blank=True, max_length=2048)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("browser", models.CharField(blank=True, max_length=100)),
                ("os", models.CharField(blank=True, max_length=100)),
                ("device_type", models.CharField(blank=True, max_length=50)),
                (
                    "link",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clicks",
                        to="links.shorturl",
                    ),
                ),
            ],
            options={
                "verbose_name": "Link Click",
                "verbose_name_plural": "Link Clicks",
                "db_table": "link_clicks",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="linkclick",
            index=models.Index(fields=["link", "timestamp"], name="link_clicks_link_ts_idx"),
        ),
        migrations.AddIndex(
            model_name="linkclick",
            index=models.Index(fields=["link", "device_type"], name="link_clicks_link_device_idx"),
        ),
    ]

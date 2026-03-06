"""Data migration — register the deactivate_expired_links periodic task."""
from django.db import migrations


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=10,
        period="minutes",
    )
    PeriodicTask.objects.get_or_create(
        name="Deactivate expired links",
        defaults={
            "task": "apps.links.tasks.deactivate_expired_links",
            "interval": schedule,
        },
    )


def delete_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Deactivate expired links").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("links", "0001_initial"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, reverse_code=delete_periodic_task),
    ]

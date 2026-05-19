"""Data migration — register the purge_guest_accounts periodic task."""

from django.db import migrations


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period="hours",
    )
    PeriodicTask.objects.get_or_create(
        name="Purge guest accounts",
        defaults={
            "task": "apps.accounts.tasks.purge_guest_accounts",
            "interval": schedule,
        },
    )


def delete_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="Purge guest accounts").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_is_guest"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, reverse_code=delete_periodic_task),
    ]

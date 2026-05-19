"""Add is_guest flag to User."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_user_managers_alter_user_groups_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_guest",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]

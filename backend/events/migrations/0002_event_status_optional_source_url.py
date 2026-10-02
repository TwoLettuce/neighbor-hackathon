from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("APPROVED", "Approved"),
                    ("PENDING", "Pending"),
                    ("REJECTED", "Rejected"),
                ],
                db_index=True,
                default="APPROVED",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="eventsourcerecord",
            name="source_url",
            field=models.URLField(blank=True, max_length=500),
        ),
    ]

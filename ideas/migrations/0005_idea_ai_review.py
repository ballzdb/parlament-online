from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ideas", "0004_moderation_and_event_archive")]

    operations = [
        migrations.AddField(
            model_name="idea",
            name="ai_review",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

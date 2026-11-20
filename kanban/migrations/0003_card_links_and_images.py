from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('kanban', '0002_task_comments_and_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='kanbancard',
            name='reference_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='kanbancard',
            name='image_url',
            field=models.URLField(blank=True),
        ),
    ]

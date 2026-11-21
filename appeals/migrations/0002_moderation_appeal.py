import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('appeals', '0001_initial'),
        ('ideas', '0004_moderation_and_event_archive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appeal',
            name='kind',
            field=models.CharField(
                choices=[
                    ('review', 'Відгук'),
                    ('proposal', 'Пропозиція'),
                    ('moderation', 'Оскарження рішення модерації'),
                ],
                default='review',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='appeal',
            name='related_idea',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='appeals',
                to='ideas.idea',
            ),
        ),
    ]

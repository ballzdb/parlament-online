from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('ideas', '0003_event'),
        ('accounts', '0006_email_verification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='idea',
            name='moderation_status',
            field=models.CharField(
                choices=[('pending', 'Очікує модерації'), ('approved', 'Опубліковано'), ('rejected', 'Відхилено модератором')],
                db_index=True, default='approved', max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='idea',
            name='moderation_status',
            field=models.CharField(
                choices=[('pending', 'Очікує модерації'), ('approved', 'Опубліковано'), ('rejected', 'Відхилено модератором')],
                db_index=True, default='pending', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='idea',
            name='moderation_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='idea',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='idea',
            name='assigned_moderator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_moderation_ideas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='idea',
            name='moderated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moderated_ideas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='idea',
            name='status',
            field=models.CharField(choices=[('submitted', 'Подано'), ('under_review', 'На розгляді'), ('in_progress', 'В роботі'), ('done', 'Виконано'), ('rejected', 'Відхилено')], default='under_review', max_length=20),
        ),
        migrations.AddField(model_name='event', name='organiser', field=models.CharField(blank=True, default='Учнівське самоврядування', max_length=160)),
        migrations.AddField(model_name='event', name='participating_classes', field=models.CharField(blank=True, help_text='Наприклад: 8-А, 9-Б, 10-А', max_length=240)),
        migrations.AddField(model_name='event', name='participant_count', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='event', name='outcome', field=models.TextField(blank=True, help_text='Підсумок або короткий звіт після проведення події')),
        migrations.AddField(model_name='event', name='updated_at', field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now), preserve_default=False),
        migrations.AddField(model_name='event', name='reference_url', field=models.URLField(blank=True)),
        migrations.AddField(model_name='event', name='image_url', field=models.URLField(blank=True)),
    ]

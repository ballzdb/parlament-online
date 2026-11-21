from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0009_user_moderator_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='additional_roles',
            field=models.JSONField(blank=True, default=list),
        ),
    ]

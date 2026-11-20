from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0006_email_verification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('student', 'Студент'),
                    ('member', 'Парламентарій'),
                    ('commission_head', 'Голова комісії'),
                    ('secretary', 'Секретар'),
                ],
                default='student',
                max_length=20,
            ),
        ),
    ]

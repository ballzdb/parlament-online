from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_user_temporary_restriction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('student', 'Студент'),
                    ('member', 'Парламентарій'),
                    ('moderator', 'Модератор'),
                    ('commission_head', 'Голова комісії'),
                    ('secretary', 'Секретар'),
                ],
                default='student',
                max_length=20,
            ),
        ),
    ]

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('accounts', '0010_user_additional_roles')]
    operations = [
        migrations.CreateModel(
            name='PendingRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True)),
                ('password_hash', models.CharField(max_length=128)),
                ('display_name', models.CharField(max_length=120)),
                ('grade', models.PositiveSmallIntegerField()),
                ('class_letter', models.CharField(blank=True, max_length=10)),
                ('token_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('last_sent_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]

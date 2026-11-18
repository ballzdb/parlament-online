from django.db import migrations, models
import django.db.models.deletion


def mark_existing_active_accounts_verified(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_active=True, email_verified_at__isnull=True).update(
        email_verified_at=models.F('date_joined')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_delete_emailallowlist_delete_emailoutbox_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('attempts_used', models.PositiveSmallIntegerField(default=0)),
                ('last_sent_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification', to='accounts.user')),
            ],
        ),
        migrations.RunPython(mark_existing_active_accounts_verified, migrations.RunPython.noop),
    ]

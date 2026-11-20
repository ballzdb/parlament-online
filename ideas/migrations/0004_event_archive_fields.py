from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('ideas', '0003_event')]
    operations = [
        migrations.AddField(model_name='event', name='organiser', field=models.CharField(blank=True, max_length=160, verbose_name='Організатор')),
        migrations.AddField(model_name='event', name='participating_classes', field=models.CharField(blank=True, max_length=300, verbose_name='Залучені класи')),
        migrations.AddField(model_name='event', name='outcome', field=models.TextField(blank=True, max_length=2000, verbose_name='Результат заходу')),
    ]
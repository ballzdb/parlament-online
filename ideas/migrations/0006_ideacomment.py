from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ideas", "0005_idea_ai_review"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IdeaComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=1200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idea_comments", to=settings.AUTH_USER_MODEL)),
                ("idea", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="ideas.idea")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]

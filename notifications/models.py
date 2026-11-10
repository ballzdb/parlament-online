from django.conf import settings
from django.db import models

from ideas.models import Idea


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    idea = models.ForeignKey(
        Idea,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    previous_status = models.CharField(max_length=20, choices=Idea.Status.choices)
    new_status = models.CharField(max_length=20, choices=Idea.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at', '-pk']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.recipient} — {self.idea}: {self.new_status}'

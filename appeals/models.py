from __future__ import annotations

from django.conf import settings
from django.db import models


class Appeal(models.Model):
    class Kind(models.TextChoices):
        REVIEW = 'review', 'Відгук'
        PROPOSAL = 'proposal', 'Пропозиція'
        MODERATION = 'moderation', 'Оскарження рішення модерації'

    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Публічний'
        PRIVATE = 'private', 'Приватний'

    class Status(models.TextChoices):
        NEW = 'new', 'Нове'
        IN_PROGRESS = 'in_progress', 'У роботі'
        RESOLVED = 'resolved', 'Вирішено'
        DECLINED = 'declined', 'Відхилено'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appeals')
    related_idea = models.ForeignKey('ideas.Idea', on_delete=models.SET_NULL, null=True, blank=True, related_name='appeals')
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.REVIEW)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    public_answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.subject} ({self.kind})'

from __future__ import annotations

from django.conf import settings
from django.db import models


class KanbanCard(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'До виконання'
        IN_PROGRESS = 'in_progress', 'У роботі'
        DONE = 'done', 'Готово'

    commission = models.ForeignKey('accounts.Commission', on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_cards')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_kanban_cards')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    due_date = models.DateField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self) -> str:
        return self.title


class TaskComment(models.Model):
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_comments')
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'Comment on {self.card_id} by {self.author_id}'

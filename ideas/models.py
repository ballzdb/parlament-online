from __future__ import annotations

from django.conf import settings
from django.db import models


class Idea(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Подано'
        UNDER_REVIEW = 'under_review', 'На розгляді'
        IN_PROGRESS = 'in_progress', 'В роботі'
        DONE = 'done', 'Виконано'
        REJECTED = 'rejected', 'Відхилено'

    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'Очікує модерації'
        APPROVED = 'approved', 'Опубліковано'
        REJECTED = 'rejected', 'Відхилено модератором'

    title = models.CharField(max_length=120)
    body = models.TextField(max_length=2000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNDER_REVIEW)
    moderation_status = models.CharField(max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    moderation_reason = models.TextField(blank=True)
    assigned_moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_moderation_ideas')
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_ideas')
    moderated_at = models.DateTimeField(null=True, blank=True)
    status_reason = models.TextField(blank=True)
    completion_report = models.TextField(blank=True)
    commission = models.ForeignKey('accounts.Commission', on_delete=models.SET_NULL, null=True, blank=True, related_name='ideas')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ideas')
    vote_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class IdeaVote(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='idea_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('idea', 'user')

    def __str__(self) -> str:
        return f'{self.user.email} -> {self.idea.title}'


class Event(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=3000, blank=True)
    starts_at = models.DateTimeField()
    organiser = models.CharField(max_length=160, blank=True, default='Учнівське самоврядування')
    participating_classes = models.CharField(max_length=240, blank=True, help_text='Наприклад: 8-А, 9-Б, 10-А')
    participant_count = models.PositiveIntegerField(null=True, blank=True)
    outcome = models.TextField(blank=True, help_text='Підсумок або короткий звіт після проведення події')
    reference_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    source_idea = models.ForeignKey(Idea, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['starts_at', 'title']

    def __str__(self) -> str:
        return self.title

from __future__ import annotations

from django.shortcuts import render

from .models import ModerationEntry


def moderation_queue(request):
    return render(request, 'moderation/queue.html', {'entries': ModerationEntry.objects.all()})

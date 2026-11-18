from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import User
from app.permissions import requires_roles
from .models import ModerationEntry


@login_required
@requires_roles(User.Role.SECRETARY)
def moderation_queue(request):
    return render(request, 'moderation/queue.html', {'entries': ModerationEntry.objects.all()})

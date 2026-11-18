from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from accounts.models import PRIMARY_ADMIN_EMAIL

from .models import EventLog


@login_required
def dashboard(request):
    if request.user.email.casefold() != PRIMARY_ADMIN_EMAIL:
        raise PermissionDenied
    return render(request, 'analytics/dashboard.html', {'events': EventLog.objects.all()[:10]})

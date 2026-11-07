from __future__ import annotations

from django.shortcuts import render

from .models import EventLog


def dashboard(request):
    return render(request, 'analytics/dashboard.html', {'events': EventLog.objects.all()[:10]})

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Appeal


def appeal_list(request):
    if request.user.is_authenticated:
        queryset = Appeal.objects.filter(author=request.user) if request.user.is_student else Appeal.objects.all()
    else:
        queryset = Appeal.objects.filter(visibility='public')
    return render(request, 'appeals/list.html', {'appeals': queryset})


@login_required
def appeal_create(request):
    return render(request, 'appeals/create.html')

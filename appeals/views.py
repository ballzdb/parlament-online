from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import AppealForm
from .models import Appeal


def appeal_list(request):
    if request.user.is_authenticated:
        queryset = Appeal.objects.filter(
            Q(author=request.user) | Q(visibility=Appeal.Visibility.PUBLIC)
        )
    else:
        queryset = Appeal.objects.filter(visibility=Appeal.Visibility.PUBLIC)
    if request.user.is_authenticated and not request.user.is_student:
        queryset = Appeal.objects.all()
    return render(request, 'appeals/list.html', {'appeals': queryset.distinct().select_related('author')})


@login_required
def appeal_create(request):
    if request.method == 'POST':
        form = AppealForm(request.POST)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.author = request.user
            appeal.save()
            messages.success(request, 'Звернення надіслано. Ваші ім’я та пошта не показуються публічно.')
            return redirect('appeals:list')
    else:
        form = AppealForm()
    return render(request, 'appeals/create.html', {'form': form})

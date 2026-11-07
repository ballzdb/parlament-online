from __future__ import annotations

from django.shortcuts import render

from .models import FAQ


def support_home(request):
    faqs = FAQ.objects.all()[:10]
    return render(request, 'support/home.html', {'faqs': faqs})

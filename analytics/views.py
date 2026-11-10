from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User

from .models import AnonymousMetric, EventLog


def dashboard(request):
    return render(request, 'analytics/dashboard.html', {'events': EventLog.objects.all()[:10]})


def classes(request):
    students = User.objects.filter(is_active=True, role=User.Role.STUDENT)
    class_counts = (
        students.filter(grade__isnull=False)
        .values('grade', 'class_letter')
        .annotate(student_count=Count('id'))
        .order_by('grade', 'class_letter')
    )
    class_rows = [
        {
            'label': f"{row['grade']}-{row['class_letter']}" if row['class_letter'] else f"{row['grade']} клас",
            'student_count': row['student_count'],
            'student_label': (
                'учень'
                if row['student_count'] % 10 == 1 and row['student_count'] % 100 != 11
                else 'учні'
                if row['student_count'] % 10 in {2, 3, 4} and row['student_count'] % 100 not in {12, 13, 14}
                else 'учнів'
            ),
        }
        for row in class_counts
    ]
    max_class_count = max((row['student_count'] for row in class_rows), default=0)
    for row in class_rows:
        row['bar_width'] = round(row['student_count'] * 100 / max_class_count) if max_class_count else 0

    total_students = students.count()
    school_size = settings.TOTAL_STUDENTS
    coverage = round(total_students * 100 / school_size) if school_size > 0 else None

    return render(request, 'analytics/classes.html', {
        'classes': class_rows,
        'total_students': total_students,
        'school_size': school_size,
        'coverage': coverage,
    })


@require_POST
def collect_anonymous_page_view(request):
    if request.headers.get('X-Anonymous-Analytics-Consent') != 'yes':
        return JsonResponse({'error': 'Потрібна згода на збір статистики.'}, status=403)

    if len(request.body) > 64:
        return JsonResponse({'error': 'Завеликий запит.'}, status=413)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Некоректний формат даних.'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Некоректний формат даних.'}, status=400)

    section = payload.get('section')
    if section not in AnonymousMetric.Section.values:
        return JsonResponse({'error': 'Невідома категорія сторінки.'}, status=400)

    metric_date = timezone.localdate()
    with transaction.atomic():
        metric, created = AnonymousMetric.objects.get_or_create(
            date=metric_date,
            section=section,
            defaults={'page_views': 1},
        )

        if not created:
            AnonymousMetric.objects.filter(pk=metric.pk).update(page_views=F('page_views') + 1)

    return JsonResponse({'status': 'recorded'}, status=202)

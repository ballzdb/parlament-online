from __future__ import annotations

import csv
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.models import PRIMARY_ADMIN_EMAIL, User
from appeals.models import Appeal
from ideas.models import Idea, IdeaVote

from .models import EventLog, PageView


def _admin_only(request):
    if request.user.email.casefold() != PRIMARY_ADMIN_EMAIL:
        raise PermissionDenied


@login_required
def dashboard(request):
    _admin_only(request)
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)

    views = PageView.objects.all()
    recent_views = views.filter(timestamp__gte=month_ago)
    daily = []
    for offset in range(29, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_views = recent_views.filter(timestamp__date=day)
        daily.append({
            'date': day.strftime('%d.%m'),
            'views': day_views.count(),
            'visitors': day_views.values('visitor_key').distinct().count(),
        })

    max_daily_views = max((item['views'] for item in daily), default=0)

    top_pages = list(
        recent_views.values('path').annotate(total=Count('id')).order_by('-total')[:10]
    )
    grade_stats = list(
        User.objects.filter(is_active=True, role=User.Role.STUDENT)
        .values('grade', 'class_letter').annotate(total=Count('id'))
        .order_by('grade', 'class_letter')
    )
    idea_statuses = list(Idea.objects.values('status').annotate(total=Count('id')).order_by('status'))
    appeal_statuses = list(Appeal.objects.values('status').annotate(total=Count('id')).order_by('status'))
    completed_ideas = Idea.objects.filter(status=Idea.Status.DONE)
    durations = [
        (item.updated_at - item.created_at).total_seconds() / 86400
        for item in completed_ideas.only('created_at', 'updated_at')
    ]
    average_idea_days = round(sum(durations) / len(durations), 1) if durations else None

    context = {
        'generated_at': now,
        'period_views': recent_views.count(),
        'period_visitors': recent_views.filter(user__isnull=False).values('user_id').distinct().count(),
        'all_views': views.count(),
        'all_visitors': views.filter(user__isnull=False).values('user_id').distinct().count(),
        'week_views': views.filter(timestamp__gte=week_ago).count(),
        'week_visitors': views.filter(timestamp__gte=week_ago, user__isnull=False).values('user_id').distinct().count(),
        'registered_students': User.objects.filter(is_active=True, role=User.Role.STUDENT).count(),
        'new_registrations': User.objects.filter(date_joined__gte=month_ago).count(),
        'active_accounts_30d': recent_views.filter(user__isnull=False).values('user_id').distinct().count(),
        'active_visitors_30d': recent_views.filter(user__isnull=False).values('user_id').distinct().count(),
        'anonymous_browsers_30d': recent_views.filter(user__isnull=True).values('visitor_key').distinct().count(),
        'top_pages': top_pages,
        'daily': daily,
        'max_daily_views': max_daily_views,
        'grade_stats': grade_stats,
        'idea_total': Idea.objects.count(),
        'idea_votes': IdeaVote.objects.count(),
        'idea_statuses': idea_statuses,
        'average_idea_days': average_idea_days,
        'appeal_total': Appeal.objects.count(),
        'appeal_statuses': appeal_statuses,
        'events': EventLog.objects.all()[:20],
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def export_csv(request):
    _admin_only(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="parlament-online-research-data.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['record_type', 'timestamp', 'path_or_category', 'metric_or_status', 'value'])
    for item in PageView.objects.order_by('timestamp').iterator():
        writer.writerow(['page_view', item.timestamp.isoformat(), item.path, 'logged_in' if item.user_id else 'anonymous', 1])
    for item in EventLog.objects.order_by('timestamp').iterator():
        writer.writerow(['event', item.timestamp.isoformat(), item.related_object, item.action, 1])
    for item in Idea.objects.order_by('created_at').iterator():
        writer.writerow(['idea', item.created_at.isoformat(), item.title, item.status, item.vote_count])
    for item in Appeal.objects.order_by('created_at').iterator():
        writer.writerow(['appeal', item.created_at.isoformat(), item.kind, item.status, 1])
    for item in IdeaVote.objects.order_by('created_at').iterator():
        writer.writerow(['vote', item.created_at.isoformat(), 'idea:' + str(item.idea_id), 'vote', 1])
    return response

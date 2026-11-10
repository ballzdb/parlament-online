from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def inbox(request):
    notifications = Notification.objects.filter(
        recipient=request.user,
    ).select_related('idea')
    page_obj = Paginator(notifications, 25).get_page(request.GET.get('page'))
    return render(request, 'notifications/inbox.html', {'page_obj': page_obj})


@login_required
@require_POST
def open_notification(request, pk):
    notification = get_object_or_404(
        Notification.objects.filter(recipient=request.user).select_related('idea'),
        pk=pk,
    )
    if not notification.is_read:
        Notification.objects.filter(pk=notification.pk, recipient=request.user).update(is_read=True)
    return redirect('ideas:detail', pk=notification.idea_id)

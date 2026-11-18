from django.contrib import admin

from accounts.models import PRIMARY_ADMIN_EMAIL
from django.urls import include, path

from ideas.views import home


def primary_admin_has_permission(request):
    user = request.user
    return bool(
        user.is_active
        and user.is_staff
        and user.is_superuser
        and user.email.casefold() == PRIMARY_ADMIN_EMAIL
    )


admin.site.has_permission = primary_admin_has_permission

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('ideas/', include('ideas.urls')),
    path('kanban/', include('kanban.urls')),
    path('appeals/', include('appeals.urls')),
    path('support/', include('support.urls')),
    path('moderation/', include('moderation.urls')),
    path('analytics/', include('analytics.urls')),
]

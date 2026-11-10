from django.contrib import admin
from django.urls import include, path

from ideas.views import decisions, home

urlpatterns = [
    path('', home, name='home'),
    path('decisions/', decisions, name='decisions'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('ideas/', include('ideas.urls')),
    path('kanban/', include('kanban.urls')),
    path('appeals/', include('appeals.urls')),
    path('support/', include('support.urls')),
    path('moderation/', include('moderation.urls')),
    path('analytics/', include('analytics.urls')),
    path('notifications/', include('notifications.urls')),
]

from django.contrib import admin

from .models import EventLog


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'related_object', 'timestamp')
    list_filter = ('action',)
    search_fields = ('related_object',)

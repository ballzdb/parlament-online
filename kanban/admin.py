from django.contrib import admin

from .models import KanbanCard


@admin.register(KanbanCard)
class KanbanCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'commission', 'status', 'assignee', 'due_date')
    list_filter = ('status', 'commission')
    search_fields = ('title', 'description')

from django.contrib import admin

from .models import KanbanCard, TaskComment


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ('author', 'created_at')


@admin.register(KanbanCard)
class KanbanCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'commission', 'status', 'assignee', 'created_by', 'due_date', 'updated_at')
    list_filter = ('status', 'commission')
    search_fields = ('title', 'description')
    inlines = (TaskCommentInline,)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('card', 'author', 'created_at')
    search_fields = ('body', 'card__title', 'author__email')
    readonly_fields = ('created_at',)

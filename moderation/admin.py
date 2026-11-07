from django.contrib import admin

from .models import ModerationEntry


@admin.register(ModerationEntry)
class ModerationEntryAdmin(admin.ModelAdmin):
    list_display = ('target_type', 'target_id', 'created_at')
    search_fields = ('target_type',)

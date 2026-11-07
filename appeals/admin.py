from django.contrib import admin

from .models import Appeal


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ('subject', 'kind', 'status', 'visibility', 'author')
    list_filter = ('kind', 'status', 'visibility')
    search_fields = ('subject', 'body')

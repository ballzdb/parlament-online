from django.contrib import admin

from .models import Idea, IdeaVote


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'commission', 'vote_count')
    list_filter = ('status', 'commission')
    search_fields = ('title', 'body')


@admin.register(IdeaVote)
class IdeaVoteAdmin(admin.ModelAdmin):
    list_display = ('idea', 'user', 'created_at')

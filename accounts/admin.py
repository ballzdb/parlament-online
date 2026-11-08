from django.contrib import admin

from .models import AuditLog, Commission, CommissionMember, SiteSettings, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name', 'role', 'is_active', 'grade')
    search_fields = ('email', 'display_name')
    list_filter = ('role', 'is_active')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('sort_order', 'name', 'slug', 'is_hidden')
    list_filter = ('is_hidden',)
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'description', 'sort_order', 'is_hidden')


@admin.register(CommissionMember)
class CommissionMemberAdmin(admin.ModelAdmin):
    list_display = ('commission', 'user', 'is_head')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'value')
    list_per_page = 50


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'email', 'user', 'created_at')
    search_fields = ('email', 'details', 'action')
    list_filter = ('action', 'created_at')
    readonly_fields = ('action', 'details', 'email', 'user', 'created_at')

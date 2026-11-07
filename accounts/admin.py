from django.contrib import admin

from .models import Commission, CommissionMember, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name', 'role', 'is_active', 'grade')
    search_fields = ('email', 'display_name')
    list_filter = ('role', 'is_active')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CommissionMember)
class CommissionMemberAdmin(admin.ModelAdmin):
    list_display = ('commission', 'user', 'is_head')

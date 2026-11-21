from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from .models import AuditLog, Commission, CommissionMember, SiteSettings, User, validate_site_url


class SiteSettingsAdminForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'

    def clean_value(self):
        value = (self.cleaned_data.get('value') or '').strip()
        if not value:
            return ''
        key = (self.cleaned_data.get('key') or '').strip()
        if key == 'contact_email':
            try:
                EmailValidator()(value)
            except ValidationError as exc:
                raise ValidationError('Введіть коректну контактну пошту.') from exc
            return value
        if not validate_site_url(value):
            raise ValidationError('Дозволені лише https:// посилання до 300 символів без javascript:/data:.')
        return value


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name', 'roles_display', 'is_active', 'grade')
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
    form = SiteSettingsAdminForm
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'value')
    list_per_page = 50
    list_filter = ('key',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'email', 'user', 'created_at')
    search_fields = ('email', 'details', 'action')
    list_filter = ('action', 'created_at')
    readonly_fields = ('action', 'details', 'email', 'user', 'created_at')

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


def validate_site_url(value: str) -> bool:
    cleaned = (value or '').strip()
    if not cleaned:
        return False
    if not cleaned.startswith('https://'):
        return False
    if len(cleaned) > 300:
        return False
    lowered = cleaned.lower()
    if 'javascript:' in lowered or 'data:' in lowered or 'vbscript:' in lowered:
        return False
    return True


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, db_index=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Role(models.TextChoices):
        STUDENT = 'student', 'Студент'
        MEMBER = 'member', 'Член парламенту'
        COMMISSION_HEAD = 'commission_head', 'Голова комісії'
        SECRETARY = 'secretary', 'Секретар'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    display_name = models.CharField(max_length=120, default='')
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    class_letter = models.CharField(max_length=10, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    anon_key = models.CharField(max_length=48, unique=True, null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)

    objects = UserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_member(self) -> bool:
        return self.role in {self.Role.MEMBER, self.Role.COMMISSION_HEAD, self.Role.SECRETARY}

    @property
    def is_commission_head(self) -> bool:
        return self.role in {self.Role.COMMISSION_HEAD, self.Role.SECRETARY}

    @property
    def is_secretary(self) -> bool:
        return self.role == self.Role.SECRETARY

    def has_role(self, *roles):
        return self.role in roles

    def requires_roles(self, *roles):
        return self.has_role(*roles)


class EmailAllowlist(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_REGISTERED = 'registered'
    STATUS_REMOVED = 'removed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Не зареєстрований'),
        (STATUS_REGISTERED, 'Зареєстрований'),
        (STATUS_REMOVED, 'Видалений'),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_invite_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['email']

    def __str__(self) -> str:
        return self.email


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField(default=timezone.now)
    attempts_used = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.email} :: {self.code}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def attempts_left(self):
        return max(0, 5 - self.attempts_used)


class EmailOutbox(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'queued'),
        (STATUS_SENT, 'sent'),
        (STATUS_FAILED, 'failed'),
    ]

    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    html_body = models.TextField(blank=True, default='')
    message_type = models.CharField(max_length=32, default='system')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    scheduled_for = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.recipient} :: {self.subject}'


class Commission(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


def seed_default_commissions():
    try:
        from django.db import OperationalError
        defaults = [
            ('Навчання', 'navchannia', 'Навчальна та освітня робота.'),
            ('Порядок', 'poryadok', 'Порядок, дисципліна та життя школи.'),
            ('Дозвілля', 'dozvillia', 'Масові заходи та дозвілля.'),
            ('Комісія 4', 'komisiya-4', 'Комісія 4.'),
            ('Комісія 5', 'komisiya-5', 'Комісія 5.'),
        ]
        for index, (name, slug, description) in enumerate(defaults):
            commission, created = Commission.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': description, 'sort_order': index, 'is_hidden': False},
            )
            if not created:
                changed = False
                if commission.name != name:
                    commission.name = name
                    changed = True
                if commission.description != description:
                    commission.description = description
                    changed = True
                if commission.sort_order != index:
                    commission.sort_order = index
                    changed = True
                if commission.is_hidden:
                    commission.is_hidden = False
                    changed = True
                if changed:
                    commission.save(update_fields=['name', 'description', 'sort_order', 'is_hidden'])
            else:
                commission.sort_order = index
                commission.save(update_fields=['sort_order'])
    except Exception:
        return


class CommissionMember(models.Model):
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commission_memberships')
    is_head = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('commission', 'user')

    def __str__(self) -> str:
        return f'{self.user.email} @ {self.commission.name}'


class SiteSettings(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.TextField(blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Налаштування сайту'
        verbose_name_plural = 'Налаштування сайту'

    def __str__(self) -> str:
        return self.key

    @classmethod
    def get_value(cls, key: str, default: str = '') -> str:
        value = cls.objects.filter(key=key).values_list('value', flat=True).first()
        return value if value is not None else default


class AuditLog(models.Model):
    action = models.CharField(max_length=80)
    details = models.TextField(blank=True, default='')
    email = models.EmailField(blank=True, default='')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Журнал аудиту'
        verbose_name_plural = 'Журнал аудиту'

    def __str__(self) -> str:
        return f'{self.action} :: {self.email or "system"}'


SITE_SETTINGS_DEFAULTS = {
    'school_site_url': 'https://lyceum.karazin.ua',
    'parliament_site_url': 'https://lyceum.karazin.ua/index.php/ua/samovryaduvannya/257-parlament-litseyu',
    'self_governance_url': 'https://lyceum.karazin.ua/index.php/ua/samovryaduvannya',
    'school_contacts_url': 'https://lyceum.karazin.ua/index.php/ua/kontaktna-informatsiya',
    'contact_email': '',
    'instagram_url': '',
    'telegram_url': '',
    'facebook_url': '',
    'tiktok_url': '',
    'youtube_url': '',
    'discord_url': '',
}


def ensure_default_site_settings():
    for key, value in SITE_SETTINGS_DEFAULTS.items():
        SiteSettings.objects.get_or_create(key=key, defaults={'value': value, 'description': key})


def get_institution_links():
    keys = {
        'school_site_url': 'Сайт ліцею',
        'parliament_site_url': 'Парламент на сайті ліцею',
        'self_governance_url': 'Самоврядування ліцею',
        'school_contacts_url': 'Контакти ліцею',
    }
    links = []
    for key, label in keys.items():
        value = SiteSettings.get_value(key, SITE_SETTINGS_DEFAULTS.get(key, '')).strip()
        if value and validate_site_url(value):
            links.append({'key': key, 'label': label, 'url': value})
    return links


def get_public_social_links():
    keys = {
        'instagram_url': 'Instagram',
        'telegram_url': 'Telegram',
        'facebook_url': 'Facebook',
        'tiktok_url': 'TikTok',
        'youtube_url': 'YouTube',
        'discord_url': 'Discord',
    }
    links = []
    for key, label in keys.items():
        value = SiteSettings.get_value(key, '').strip()
        if validate_site_url(value):
            links.append({'key': key, 'label': label, 'url': value})
    return links

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


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


class Commission(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


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

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def normalize_phone(value: str) -> str:
    """Remove common separators so '+48 123-456-789' and '123456789' match."""
    return re.sub(r'[\s\-/().]', '', value or '')


def validate_pl_phone(value: str) -> None:
    """Accept 9 digits with optional +48 prefix after normalization."""
    normalized = normalize_phone(value)
    if not re.fullmatch(r'(\+48)?\d{9}', normalized):
        raise ValidationError(
            'Enter a valid Polish phone number: 9 digits, optional +48 prefix.'
        )


class ContactStatus(models.Model):
    """Lookup table for contact statuses (editable via DB/admin)."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'contact statuses'

    def __str__(self) -> str:
        return self.name


class Contact(models.Model):
    """A single contact. Phone and email are unique across all contacts."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True, validators=[validate_pl_phone])
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=100)
    status = models.ForeignKey(
        ContactStatus, on_delete=models.PROTECT, related_name='contacts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Used later by auth isolation (#11): owner is null until login is added.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
    )
    is_shared = models.BooleanField(default=False)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name} ({self.city})'

    def clean(self) -> None:
        super().clean()
        # Normalize before uniqueness check so formatted duplicates collide.
        self.phone = normalize_phone(self.phone)
        if self.email:
            self.email = self.email.strip().lower()
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.city:
            self.city = self.city.strip()

    def save(self, *args, **kwargs):
        # Enforce normalization + uniqueness also for direct .create() calls.
        self.full_clean()
        return super().save(*args, **kwargs)

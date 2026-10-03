import csv
import io

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Contact, ContactStatus, normalize_phone

REQUIRED_COLUMNS = {'first_name', 'last_name', 'phone', 'email', 'city', 'status'}


def import_contacts_from_csv(uploaded_file) -> tuple[int, int]:
    """Parse CSV and create contacts. Returns (added, skipped).

    - Encoding utf-8-sig (handles BOM from Excel).
    - Skips rows with missing columns, invalid data or duplicates.
    - Status is looked up case-insensitively, created if missing.
    """
    text = io.TextIOWrapper(uploaded_file, encoding='utf-8-sig')
    reader = csv.DictReader(text)
    if reader.fieldnames is None:
        raise ValidationError('Empty CSV file.')
    missing = REQUIRED_COLUMNS - {h.strip() for h in reader.fieldnames if h}
    if missing:
        raise ValidationError(f'Missing columns: {", ".join(sorted(missing))}.')

    added = 0
    skipped = 0
    for row in reader:
        try:
            first_name = (row.get('first_name') or '').strip()
            last_name = (row.get('last_name') or '').strip()
            phone = normalize_phone(row.get('phone') or '')
            email = (row.get('email') or '').strip().lower()
            city = (row.get('city') or '').strip()
            status_name = (row.get('status') or '').strip()
            if not all([first_name, last_name, phone, email, city, status_name]):
                skipped += 1
                continue
            if Contact.objects.filter(phone=phone).exists():
                skipped += 1
                continue
            if Contact.objects.filter(email__iexact=email).exists():
                skipped += 1
                continue
            status, _ = ContactStatus.objects.get_or_create(name=status_name)
            contact = Contact(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                city=city,
                status=status,
            )
            contact.full_clean()
            contact.save()
            added += 1
        except (ValidationError, IntegrityError, ValueError):
            skipped += 1
    return added, skipped

import csv
import io

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Contact, ContactStatus, normalize_phone

REQUIRED_COLUMNS = {'first_name', 'last_name', 'phone', 'email', 'city', 'status'}


def import_contacts_from_csv(uploaded_file, owner=None):
    """Parse CSV and create contacts.

    Returns (added, skipped, skipped_rows) where skipped_rows is a list of
    (csv_row_number, reason) tuples for the import report.
    Encoding utf-8-sig (handles BOM from Excel).
    """
    text = io.TextIOWrapper(uploaded_file, encoding='utf-8-sig')
    reader = csv.DictReader(text)
    if reader.fieldnames is None:
        raise ValidationError('Empty CSV file.')
    missing = REQUIRED_COLUMNS - {h.strip() for h in reader.fieldnames if h}
    if missing:
        raise ValidationError(f'Missing columns: {", ".join(sorted(missing))}.')

    added = 0
    skipped_rows = []
    # Row numbers match the file lines: line 1 is the header row.
    for line_number, row in enumerate(reader, start=2):
        reason = None
        try:
            first_name = (row.get('first_name') or '').strip()
            last_name = (row.get('last_name') or '').strip()
            phone = normalize_phone(row.get('phone') or '')
            email = (row.get('email') or '').strip().lower()
            city = (row.get('city') or '').strip()
            status_name = (row.get('status') or '').strip()
            if not all([first_name, last_name, phone, email, city, status_name]):
                reason = 'Missing required value.'
            elif Contact.objects.filter(phone=phone).exists():
                reason = 'Duplicate phone number.'
            elif Contact.objects.filter(email__iexact=email).exists():
                reason = 'Duplicate email address.'
            else:
                # Unknown CSV statuses become new rows, so nothing is lost.
                status, _ = ContactStatus.objects.get_or_create(name=status_name)
                contact = Contact(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    city=city,
                    status=status,
                    owner=owner,
                )
                contact.full_clean()
                contact.save()
                added += 1
        except (ValidationError, IntegrityError, ValueError) as exc:
            reason = str(exc) if str(exc) else 'Invalid row.'
        if reason is not None:
            skipped_rows.append((line_number, reason))
    return added, len(skipped_rows), skipped_rows

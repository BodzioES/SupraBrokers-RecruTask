from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from .models import Contact, ContactStatus
from .services import import_contacts_from_csv


def make_status(name='new'):
    obj, _ = ContactStatus.objects.get_or_create(name=name)
    return obj


def make_contact(**kwargs):
    defaults = {
        'first_name': 'Jan',
        'last_name': 'Kowalski',
        'phone': '123456789',
        'email': 'jan@example.com',
        'city': 'Warszawa',
    }
    defaults.update(kwargs)
    if 'status' not in defaults:
        defaults['status'] = make_status()
    return Contact.objects.create(**defaults)


class ContactModelTest(TestCase):
    """Phone numbers are unique (normalization included)."""

    def test_duplicate_phone_is_rejected(self):
        make_contact(phone='123456789', email='a@example.com')
        with self.assertRaises(Exception):
            make_contact(phone='123 456 789', email='b@example.com')


class ContactApiTest(APITestCase):
    """CRUD through /api/contacts/."""

    def setUp(self):
        self.user = User.objects.create_user('apiuser', password='pass')
        self.client.force_authenticate(user=self.user)
        self.status = make_status()
        self.contact = make_contact(status=self.status, owner=self.user)

    def test_create_update_delete(self):
        create_url = '/api/contacts/'
        payload = {
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'phone': '987654321',
            'email': 'anna@example.com',
            'city': 'Gdansk',
            'status': self.status.id,
        }
        created = self.client.post(create_url, payload, format='json')
        self.assertEqual(created.status_code, http_status.HTTP_201_CREATED)

        detail_url = f'/api/contacts/{created.data["id"]}/'
        updated = self.client.put(
            detail_url, {**payload, 'city': 'Sopot'}, format='json'
        )
        self.assertEqual(updated.status_code, http_status.HTTP_200_OK)
        self.assertEqual(updated.data['city'], 'Sopot')

        deleted = self.client.delete(detail_url)
        self.assertEqual(deleted.status_code, http_status.HTTP_204_NO_CONTENT)


class CsvImportTest(TestCase):
    """CSV import creates new contacts and reports skipped rows."""

    def test_import_adds_and_skips_duplicates(self):
        make_contact(phone='123456789', email='jan@example.com')
        csv_content = (
            'first_name,last_name,phone,email,city,status\n'
            'Jan,Kowalski,123456789,jan@example.com,Warszawa,new\n'
            'Ewa,Kowal,555666777,ewa@example.com,Poznan,new\n'
        )
        uploaded = SimpleUploadedFile(
            'contacts.csv', csv_content.encode('utf-8'), content_type='text/csv'
        )
        added, duplicates, invalid, skipped_rows = import_contacts_from_csv(uploaded)
        self.assertEqual((added, duplicates, invalid), (1, 1, 0))
        self.assertEqual(len(skipped_rows), 1)
        self.assertIn('Duplicate', skipped_rows[0][1])
        self.assertTrue(Contact.objects.filter(email='ewa@example.com').exists())

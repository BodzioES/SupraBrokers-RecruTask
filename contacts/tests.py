from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from .models import Contact, ContactStatus
from .services import import_contacts_from_csv
from .views import filter_contacts


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
        added, skipped, skipped_rows = import_contacts_from_csv(uploaded)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(skipped_rows), 1)
        self.assertIn('Duplicate', skipped_rows[0][1])
        self.assertTrue(Contact.objects.filter(email='ewa@example.com').exists())

    def test_import_reports_reasons(self):
        csv_content = (
            'first_name,last_name,phone,email,city,status\n'
            'Anna,Nowak,111222333,anna@example.com,Krakow,new\n'
            'Anna,Nowak,111222333,anna@example.com,Krakow,new\n'
            'Jan,Kowalski,444555666,not-an-email,Warszawa,new\n'
        )
        uploaded = SimpleUploadedFile(
            'contacts.csv', csv_content.encode('utf-8'), content_type='text/csv'
        )
        added, skipped, skipped_rows = import_contacts_from_csv(uploaded)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 2)
        reasons = [reason for _, reason in skipped_rows]
        self.assertTrue(any('Duplicate' in reason for reason in reasons))


class ContactIsolationTest(TestCase):
    """Users do not see other users' private contacts."""

    def test_user_does_not_see_others_private_contacts(self):
        user_a = User.objects.create_user('alice', password='pass')
        user_b = User.objects.create_user('bob', password='pass')
        private_b = make_contact(
            phone='111111111', email='b@example.com',
            status=make_status(), owner=user_b, is_shared=False,
        )
        self.client.force_login(user_a)
        response = self.client.get(reverse('contacts:list'))
        self.assertNotIn(private_b, list(response.context['contacts']))


class UnaccentSearchTest(TestCase):
    """Searching without diacritics finds contacts with diacritics."""

    def test_ascii_query_finds_diacritic_contact(self):
        user = User.objects.create_user('searcher', password='pass')
        contact = make_contact(
            first_name='Łukasz', last_name='Żuk', city='Kraków',
            phone='444444444', email='lukasz@example.com',
            status=make_status(), owner=user,
        )
        results = filter_contacts({'q': 'Krakow'}, user)
        self.assertIn(contact, list(results))

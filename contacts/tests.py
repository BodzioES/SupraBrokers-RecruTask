from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
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
    """Unique phone/email are enforced."""

    def test_duplicate_phone_is_rejected(self):
        make_contact(phone='123456789', email='a@example.com')
        with self.assertRaises(Exception):
            make_contact(phone='123 456 789', email='b@example.com')

    def test_duplicate_email_is_rejected(self):
        make_contact(phone='111111111', email='Jan@Example.com')
        with self.assertRaises(Exception):
            make_contact(phone='222222222', email='jan@example.com')

    def test_phone_is_normalized_on_clean(self):
        contact = Contact(
            first_name='A',
            last_name='B',
            phone='+48 123-456-789',
            email='a@b.com',
            city='Krakow',
            status=make_status(),
        )
        contact.full_clean()
        self.assertEqual(contact.phone, '+48123456789')


class ContactApiTest(APITestCase):
    """CRUD through /api/contacts/."""

    def setUp(self):
        self.status = make_status()
        self.contact = make_contact(status=self.status)

    def test_list_returns_required_fields(self):
        response = self.client.get('/api/contacts/')
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertTrue(len(results) >= 1)
        item = results[0]
        for field in ('id', 'first_name', 'last_name', 'city', 'status', 'created_at'):
            self.assertIn(field, item)

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

    def test_list_page_is_accessible_via_named_url(self):
        self.assertEqual(reverse('contacts:list'), '/')


class CsvImportTest(TestCase):
    """CSV import creates new contacts and skips duplicates."""

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
        added, skipped = import_contacts_from_csv(uploaded)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 1)
        self.assertTrue(Contact.objects.filter(email='ewa@example.com').exists())


class ContactIsolationTest(TestCase):
    """Users see own or shared contacts; others' private ones stay hidden."""

    def setUp(self):
        self.user_a = User.objects.create_user('alice', password='pass')
        self.user_b = User.objects.create_user('bob', password='pass')
        status = make_status()
        self.private_b = make_contact(
            phone='111111111', email='b@example.com', status=status,
            owner=self.user_b, is_shared=False,
        )
        self.shared_a = make_contact(
            phone='222222222', email='shared@example.com', status=status,
            owner=self.user_a, is_shared=True,
        )

    def test_user_does_not_see_others_private_contacts(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('contacts:list'))
        contacts = list(response.context['contacts'])
        self.assertIn(self.shared_a, contacts)
        self.assertNotIn(self.private_b, contacts)

    def test_user_cannot_edit_others_private_contact(self):
        self.client.force_login(self.user_a)
        url = reverse('contacts:edit', args=[self.private_b.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_login_is_required(self):
        self.assertEqual(self.client.get(reverse('contacts:list')).status_code, 302)

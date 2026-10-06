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
        self.user = User.objects.create_user('apiuser', password='pass')
        self.client.force_authenticate(user=self.user)
        self.status = make_status()
        self.contact = make_contact(status=self.status, owner=self.user)

    def test_anonymous_is_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/contacts/')
        self.assertIn(
            response.status_code,
            (http_status.HTTP_401_UNAUTHORIZED, http_status.HTTP_403_FORBIDDEN),
        )

    def test_private_contact_of_other_user_is_hidden(self):
        other = User.objects.create_user('other', password='pass')
        hidden = make_contact(
            phone='333333333', email='other@example.com',
            status=self.status, owner=other,
        )
        response = self.client.get('/api/contacts/')
        ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(hidden.id, ids)
        detail = self.client.get(f'/api/contacts/{hidden.id}/')
        self.assertEqual(detail.status_code, http_status.HTTP_404_NOT_FOUND)

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
        added, skipped, skipped_rows = import_contacts_from_csv(uploaded)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(skipped_rows), 1)
        self.assertIn('Duplicate', skipped_rows[0][1])
        self.assertTrue(Contact.objects.filter(email='ewa@example.com').exists())

    def test_import_reports_reasons_and_handles_bom(self):
        csv_content = (
            'first_name,last_name,phone,email,city,status\n'
            'Anna,Dąbrowska,111222333,anna@example.com,Kraków,new\n'
            'Anna,Dąbrowska,111222333,anna@example.com,Kraków,new\n'
            'Jan,Kowalski,444555666,not-an-email,Warszawa,new\n'
        )
        import codecs

        uploaded = SimpleUploadedFile(
            'contacts.csv',
            codecs.BOM_UTF8 + csv_content.encode('utf-8'),
            content_type='text/csv',
        )
        added, skipped, skipped_rows = import_contacts_from_csv(uploaded)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 2)
        reasons = [reason for _, reason in skipped_rows]
        self.assertTrue(any('Duplicate' in reason for reason in reasons))
        contact = Contact.objects.get(email='anna@example.com')
        self.assertEqual(contact.city, 'Kraków')


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


class AvatarInitialsTest(TestCase):
    """Initials handle Polish letters; color is deterministic."""

    def test_initials_with_diacritics(self):
        contact = make_contact(first_name='Łukasz', last_name='Żuk')
        self.assertEqual(contact.initials, 'ŁŻ')

    def test_avatar_color_is_deterministic(self):
        first = make_contact(first_name='Anna', last_name='Nowak').avatar_color
        second = make_contact(
            first_name='Anna', last_name='Nowak',
            phone='999999999', email='other@example.com',
        ).avatar_color
        self.assertEqual(first, second)
        self.assertIn(first, range(8))


class WeatherCacheTest(TestCase):
    """City key normalization and short negative cache for misses."""

    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_city_key_ignores_case_and_diacritics(self):
        from .weather import normalize_city_key

        self.assertEqual(normalize_city_key('Kraków'), normalize_city_key('krakow'))
        self.assertEqual(normalize_city_key('Łódź'), normalize_city_key('lodz'))

    def test_unknown_city_is_cached_negatively(self):
        from unittest import mock

        from . import weather as weather_module

        with mock.patch.object(
            weather_module, '_fetch_json', return_value=[]
        ) as fetch:
            self.assertIsNone(weather_module.get_city_weather('NoSuchCityXYZ'))
            self.assertIsNone(weather_module.get_city_weather('NoSuchCityXYZ'))
            self.assertEqual(fetch.call_count, 1)

    def test_weather_result_has_code_and_timestamp(self):
        from unittest import mock

        from . import weather as weather_module

        geo = [{'lat': '52.23', 'lon': '21.01'}]
        meteo = {
            'current': {
                'temperature_2m': 16.5,
                'relative_humidity_2m': 63,
                'wind_speed_10m': 2.9,
                'weather_code': 2,
            }
        }
        with mock.patch.object(
            weather_module, '_fetch_json', side_effect=[geo, meteo]
        ):
            result = weather_module.get_city_weather('Warszawa')
        self.assertEqual(result['weather_code'], 2)
        self.assertIn('fetched_at', result)


class UnaccentSearchTest(TestCase):
    """Diacritics work both ways: Krakow finds Kraków and vice versa."""

    def setUp(self):
        self.user = User.objects.create_user('searcher', password='pass')
        self.contact = make_contact(
            first_name='Łukasz', last_name='Żuk', city='Kraków',
            phone='444444444', email='lukasz@example.com',
            status=make_status(), owner=self.user,
        )

    def test_ascii_query_finds_diacritic_contact(self):
        results = filter_contacts({'q': 'Krakow'}, self.user)
        self.assertIn(self.contact, list(results))
        results = filter_contacts({'q': 'Lukasz'}, self.user)
        self.assertIn(self.contact, list(results))

    def test_diacritic_query_finds_contact(self):
        results = filter_contacts({'q': 'Kraków'}, self.user)
        self.assertIn(self.contact, list(results))
        results = filter_contacts({'q': 'Żuk'}, self.user)
        self.assertIn(self.contact, list(results))


class FilterTest(TestCase):
    """Status/city filters narrow results; invalid values are ignored."""

    def setUp(self):
        self.user = User.objects.create_user('filterer', password='pass')
        self.status = make_status()
        other_status = make_status('lost')
        self.warsaw = make_contact(
            phone='777111222', email='w@example.com', city='Warszawa',
            status=self.status, owner=self.user,
        )
        make_contact(
            phone='777111333', email='g@example.com', city='Gdansk',
            status=other_status, owner=self.user,
        )

    def test_filter_by_status(self):
        results = filter_contacts({'status': str(self.status.id)}, self.user)
        self.assertIn(self.warsaw, list(results))
        self.assertEqual(len(list(results)), 1)

    def test_filter_by_city_case_insensitive(self):
        results = filter_contacts({'city': 'warszawa'}, self.user)
        self.assertIn(self.warsaw, list(results))
        self.assertEqual(len(list(results)), 1)

    def test_invalid_filter_values_are_ignored(self):
        results = filter_contacts({'status': 'nope', 'city': ''}, self.user)
        self.assertEqual(len(list(results)), 2)

import random
import unicodedata

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from contacts.models import Contact, ContactStatus

# Gender-matched first/last name pairs with correct Polish diacritics.
NAME_PAIRS = [
    ('Anna', 'Dąbrowska'),
    ('Łukasz', 'Kowalski'),
    ('Agnieszka', 'Kowalska'),
    ('Małgorzata', 'Wiśniewska'),
    ('Paweł', 'Wójcik'),
    ('Zuzanna', 'Kamińska'),
    ('Józef', 'Żak'),
    ('Katarzyna', 'Zielińska'),
    ('Marek', 'Lewandowski'),
    ('Ewa', 'Szymańska'),
    ('Tomasz', 'Woźniak'),
    ('Magdalena', 'Dąbrowska'),
    ('Michał', 'Kozłowski'),
    ('Natalia', 'Jankowska'),
    ('Adam', 'Mazur'),
    ('Paulina', 'Wojciechowska'),
    ('Bartosz', 'Krawczyk'),
    ('Karolina', 'Piotrowska'),
    ('Kamil', 'Grabowski'),
    ('Monika', 'Nowakowska'),
    ('Damian', 'Pawłowski'),
    ('Sylwia', 'Kamińska'),
    ('Jan', 'Kowalczyk'),
    ('Piotr', 'Nowak'),
]
CITIES = [
    'Warszawa', 'Kraków', 'Gdańsk', 'Wrocław', 'Poznań', 'Łódź',
    'Szczecin', 'Katowice', 'Lublin', 'Gdynia', 'Białystok',
]


def ascii_email_part(value: str) -> str:
    """Strip diacritics so generated emails stay plain ASCII."""
    normalized = unicodedata.normalize('NFKD', value)
    stripped = ''.join(c for c in normalized if not unicodedata.combining(c))
    return stripped.replace('ł', 'l').replace('Ł', 'L').lower()


class Command(BaseCommand):
    help = 'Create N random contacts for UI testing (default: 20).'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20)

    def handle(self, *args, **options):
        """Create up to count new unique people (top-up, never duplicates)."""
        count = options['count']
        statuses = list(ContactStatus.objects.all())
        if not statuses:
            self.stderr.write('No statuses in DB. Run migrations first.')
            return
        try:
            owner = User.objects.get(username='test')
        except User.DoesNotExist:
            owner = None

        # People already in the DB count too, so re-runs only top up.
        # One person appears only once, no matter the city.
        existing_people = set(
            Contact.objects.values_list('first_name', 'last_name')
        )
        target_total = len(existing_people) + count
        created = 0
        attempts = 0
        # Attempts cap the loop: random duplicates must not loop forever.
        while (
            len(existing_people) < target_total and attempts < count * 20
        ):
            attempts += 1
            phone = ''.join(random.choices('0123456789', k=9))
            if random.random() < 0.3:
                phone = '+48' + phone
            first_name, last_name = random.choice(NAME_PAIRS)
            if (first_name, last_name) in existing_people:
                continue
            city = random.choice(CITIES)
            email = (
                f'{ascii_email_part(first_name)}.{ascii_email_part(last_name)}'
                f'{random.randint(1, 9999)}@example.com'
            )
            if Contact.objects.filter(phone=phone.replace(' ', '')).exists():
                continue
            if Contact.objects.filter(email__iexact=email).exists():
                continue
            Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                city=city,
                status=random.choice(statuses),
                owner=owner,
                # Without a demo user the contacts stay visible to everyone.
                is_shared=owner is None,
            )
            existing_people.add((first_name, last_name))
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} contacts.'))

import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from contacts.models import Contact, ContactStatus

FIRST_NAMES = [
    'Jan', 'Anna', 'Piotr', 'Katarzyna', 'Marek', 'Agnieszka', 'Tomasz',
    'Magdalena', 'Michal', 'Ewa', 'Lukasz', 'Natalia', 'Adam', 'Paulina',
    'Bartosz', 'Karolina', 'Kamil', 'Monika', 'Damian', 'Sylwia',
]
LAST_NAMES = [
    'Kowalski', 'Nowak', 'Zielinski', 'Wisniewski', 'Wojcik', 'Kaminski',
    'Lewandowski', 'Szymanski', 'Wozniak', 'Dabrowski', 'Kozlowski',
    'Jankowski', 'Mazur', 'Wojciechowski', 'Kwiatkowski', 'Krawczyk',
    'Piotrowski', 'Grabowski', 'Nowakowski', 'Pawlowski',
]
CITIES = [
    'Warszawa', 'Krakow', 'Gdansk', 'Wroclaw', 'Poznan', 'Lodz',
    'Szczecin', 'Katowice', 'Lublin', 'Gdynia',
]


class Command(BaseCommand):
    help = 'Create N random contacts for UI testing (default: 20).'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20)

    def handle(self, *args, **options):
        count = options['count']
        statuses = list(ContactStatus.objects.all())
        if not statuses:
            self.stderr.write('No statuses in DB. Run migrations first.')
            return
        try:
            owner = User.objects.get(username='test')
        except User.DoesNotExist:
            owner = None

        created = 0
        attempts = 0
        while created < count and attempts < count * 20:
            attempts += 1
            phone = ''.join(random.choices('0123456789', k=9))
            if random.random() < 0.3:
                phone = '+48' + phone
            email = (
                f'{random.choice(FIRST_NAMES).lower()}.'
                f'{random.choice(LAST_NAMES).lower()}{random.randint(1, 9999)}'
                '@example.com'
            )
            if Contact.objects.filter(phone=phone.replace(' ', '')).exists():
                continue
            if Contact.objects.filter(email__iexact=email).exists():
                continue
            Contact.objects.create(
                first_name=random.choice(FIRST_NAMES),
                last_name=random.choice(LAST_NAMES),
                phone=phone,
                email=email,
                city=random.choice(CITIES),
                status=random.choice(statuses),
                owner=owner,
                is_shared=owner is None,
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} contacts.'))

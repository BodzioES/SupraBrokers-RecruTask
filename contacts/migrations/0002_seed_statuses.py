from django.db import migrations


DEFAULT_STATUSES = ['new', 'in_progress', 'lost', 'outdated']


def seed_statuses(apps, schema_editor):
    ContactStatus = apps.get_model('contacts', 'ContactStatus')
    for name in DEFAULT_STATUSES:
        ContactStatus.objects.get_or_create(name=name)


def unseed_statuses(apps, schema_editor):
    ContactStatus = apps.get_model('contacts', 'ContactStatus')
    ContactStatus.objects.filter(name__in=DEFAULT_STATUSES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_statuses, unseed_statuses),
    ]

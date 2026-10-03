from django.db import migrations


def share_ownerless(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')
    Contact.objects.filter(owner__isnull=True).update(is_shared=True)


class Migration(migrations.Migration):
    dependencies = [
        ('contacts', '0002_seed_statuses'),
    ]

    operations = [
        migrations.RunPython(share_ownerless, migrations.RunPython.noop),
    ]

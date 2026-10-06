from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('contacts', '0003_share_ownerless_contacts'),
    ]

    operations = [
        # Enables accent-insensitive search (Krakow matches Kraków).
        # Requires a Postgres user allowed to create extensions.
        UnaccentExtension(),
    ]

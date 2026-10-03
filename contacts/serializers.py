from rest_framework import serializers

from .models import Contact, normalize_phone, validate_pl_phone


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for list/create/update. Status is writable by id."""

    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone',
            'email',
            'city',
            'status',
            'status_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'status_name']

    def validate_phone(self, value: str) -> str:
        validate_pl_phone(value)
        return normalize_phone(value)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

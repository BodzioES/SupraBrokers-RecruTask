from rest_framework import serializers

from .models import Contact, ContactStatus, normalize_phone, validate_pl_phone


class StatusIdOrNameField(serializers.Field):
    """Accept a status id (e.g. 1) or a status name (e.g. "new")."""

    def to_representation(self, value) -> int:
        return value.pk

    def to_internal_value(self, data) -> ContactStatus:
        lookup = str(data).strip() if data is not None else ''
        status = None
        if lookup.isdigit():
            status = ContactStatus.objects.filter(pk=int(lookup)).first()
        if status is None and lookup:
            status = ContactStatus.objects.filter(name__iexact=lookup).first()
        if status is None:
            raise serializers.ValidationError(
                f'Unknown status: {data!r}. Use an id or a status name.'
            )
        return status


class ContactListSerializer(serializers.ModelSerializer):
    """Slim serializer for GET /api/contacts/ (spec fields + status_name)."""

    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'last_name',
            'city',
            'status',
            'status_name',
            'created_at',
        ]
        read_only_fields = fields


class ContactSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update. Status by id or name."""

    status = StatusIdOrNameField()
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

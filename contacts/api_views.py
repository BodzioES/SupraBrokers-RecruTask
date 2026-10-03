from rest_framework import viewsets

from .models import Contact
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """Provides GET/POST /api/contacts/ and PUT/DELETE /api/contacts/{id}/."""

    queryset = Contact.objects.select_related('status').order_by('last_name', 'id')
    serializer_class = ContactSerializer

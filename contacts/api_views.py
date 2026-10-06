from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Contact
from .serializers import ContactSerializer
from .views import visible_contacts


class ContactViewSet(viewsets.ModelViewSet):
    """Provides GET/POST /api/contacts/ and PUT/DELETE /api/contacts/{id}/."""

    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Same isolation as the UI: own or shared contacts only.
        return visible_contacts(self.request.user).order_by('last_name', 'id')

    def perform_create(self, serializer):
        # New API contacts belong to the logged-in user by default.
        serializer.save(owner=self.request.user)

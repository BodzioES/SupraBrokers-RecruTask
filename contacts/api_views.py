from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import Contact
from .serializers import ContactListSerializer, ContactSerializer
from .views import visible_contacts


class OptionalPagination(PageNumberPagination):
    """Paginate only when ?page= or ?page_size= is given.

    Otherwise the list returns a plain JSON array of all contacts.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # None means "no pagination": DRF then returns a plain list.
        if 'page' not in request.query_params and (
            'page_size' not in request.query_params
        ):
            return None
        return super().paginate_queryset(queryset, request, view)


class ContactViewSet(viewsets.ModelViewSet):
    """Provides GET/POST /api/contacts/ and PUT/DELETE /api/contacts/{id}/."""

    permission_classes = [IsAuthenticated]
    pagination_class = OptionalPagination

    def get_serializer_class(self):
        # Slim list per spec; full details for retrieve/create/update.
        if self.action == 'list':
            return ContactListSerializer
        return ContactSerializer

    def get_queryset(self):
        # Same isolation as the UI: own or shared contacts only.
        return visible_contacts(self.request.user).order_by('last_name', 'id')

    def perform_create(self, serializer):
        # New API contacts belong to the logged-in user by default.
        serializer.save(owner=self.request.user)

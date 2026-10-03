from django.db.models import Q
from django.views.generic import ListView

from .models import Contact


class ContactListView(ListView):
    """Paginated, searchable and sortable contact list."""

    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 10

    allowed_sorts = ('last_name', 'created_at')

    def get_sort(self) -> tuple[str, str]:
        sort = self.request.GET.get('sort', 'last_name')
        if sort not in self.allowed_sorts:
            sort = 'last_name'
        order = self.request.GET.get('order', 'asc')
        if order not in ('asc', 'desc'):
            order = 'asc'
        return sort, order

    def get_queryset(self):
        qs = Contact.objects.select_related('status').all()
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(city__icontains=query)
                | Q(phone__icontains=query)
            )
        sort, order = self.get_sort()
        prefix = '' if order == 'asc' else '-'
        return qs.order_by(f'{prefix}{sort}', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort, order = self.get_sort()
        context['q'] = self.request.GET.get('q', '')
        context['sort'] = sort
        context['order'] = order
        context['next_order'] = 'desc' if order == 'asc' else 'asc'
        return context

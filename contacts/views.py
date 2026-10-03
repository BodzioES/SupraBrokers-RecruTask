import json

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ContactForm, ContactImportForm
from .models import Contact
from .services import import_contacts_from_csv


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


class ContactCreateView(SuccessMessageMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')
    success_message = 'Contact %(first_name)s %(last_name)s was created.'


class ContactUpdateView(SuccessMessageMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')
    success_message = 'Contact %(first_name)s %(last_name)s was updated.'


class ContactDeleteView(DeleteView):
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:list')


class ContactImportView(FormView):
    form_class = ContactImportForm
    template_name = 'contacts/contact_import.html'
    success_url = reverse_lazy('contacts:list')

    def form_valid(self, form):
        try:
            added, skipped = import_contacts_from_csv(form.cleaned_data['file'])
        except ValidationError as exc:
            form.add_error('file', exc)
            return self.form_invalid(form)
        messages.success(
            self.request, f'Imported {added} contacts, skipped {skipped}.'
        )
        return super().form_valid(form)


class DashboardView(TemplateView):
    """Simple stats: contacts per city chart data."""

    template_name = 'contacts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = list(
            Contact.objects.values('city')
            .annotate(total=Count('id'))
            .order_by('-total', 'city')
        )
        context['city_stats'] = stats
        context['total_contacts'] = Contact.objects.count()
        context['chart_data'] = json.dumps(
            {'labels': [s['city'] for s in stats], 'data': [s['total'] for s in stats]}
        )
        return context

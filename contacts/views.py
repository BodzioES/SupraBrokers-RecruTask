from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ContactForm, ContactImportForm
from .models import Contact, ContactStatus
from .services import import_contacts_from_csv
from .services.weather import get_city_weather

ALLOWED_SORTS = ('last_name', 'created_at')


def visible_contacts(user) -> object:
    """Isolation: superusers see everything, others see own or shared."""
    qs = Contact.objects.select_related('status').all()
    if user.is_superuser:
        return qs
    return qs.filter(Q(owner=user) | Q(is_shared=True))


def filter_contacts(params, user) -> object:
    """Apply visibility plus search and sorting."""
    qs = visible_contacts(user)
    query = params.get('q', '').strip()
    if query:
        qs = qs.filter(
                Q(first_name__unaccent__icontains=query)
                | Q(last_name__unaccent__icontains=query)
                | Q(email__icontains=query)
                | Q(city__unaccent__icontains=query)
                | Q(phone__icontains=query)
            )
    sort = params.get('sort', 'last_name')
    if sort not in ALLOWED_SORTS:
        sort = 'last_name'
    order = params.get('order', 'asc')
    if order not in ('asc', 'desc'):
        order = 'asc'
    prefix = '' if order == 'asc' else '-'
    return qs.order_by(f'{prefix}{sort}', 'id')


class ContactListView(LoginRequiredMixin, ListView):
    """Paginated, searchable and sortable contact list."""

    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 10

    allowed_sorts = ALLOWED_SORTS

    def get_sort(self) -> tuple[str, str]:
        # Only whitelisted values pass through, so raw GET params
        # can never inject an arbitrary field into order_by().
        sort = self.request.GET.get('sort', 'last_name')
        if sort not in self.allowed_sorts:
            sort = 'last_name'
        order = self.request.GET.get('order', 'asc')
        if order not in ('asc', 'desc'):
            order = 'asc'
        return sort, order

    def get_queryset(self):
        return filter_contacts(self.request.GET, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort, order = self.get_sort()
        context['q'] = self.request.GET.get('q', '')
        context['sort'] = sort
        context['order'] = order
        context['next_order'] = 'desc' if order == 'asc' else 'asc'
        context['statuses'] = ContactStatus.objects.all()
        return context


class ContactCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')
    success_message = 'Contact %(first_name)s %(last_name)s was created.'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnedContactMixin:
    """Limit edit/delete to contacts the user may manage (own or shared)."""

    def get_queryset(self):
        return visible_contacts(self.request.user)


class ContactUpdateView(
    LoginRequiredMixin, OwnedContactMixin, SuccessMessageMixin, UpdateView
):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')
    success_message = 'Contact %(first_name)s %(last_name)s was updated.'


class ContactDeleteView(LoginRequiredMixin, OwnedContactMixin, DeleteView):
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:list')


class ContactImportView(LoginRequiredMixin, FormView):
    """Upload a CSV file. Result is shown as toasts (counts + row reasons)."""

    form_class = ContactImportForm
    template_name = 'contacts/contact_import.html'
    success_url = reverse_lazy('contacts:list')

    def form_valid(self, form):
        try:
            added, duplicates, invalid, skipped_rows = import_contacts_from_csv(
                form.cleaned_data['file'], owner=self.request.user
            )
        except ValidationError as exc:
            form.add_error('file', exc)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f'Imported {added} contacts, '
            f'{duplicates} duplicates, {invalid} invalid rows.',
        )
        # Cap the per-row warnings so one bad file cannot flood the page.
        for line_number, reason in skipped_rows[:20]:
            messages.warning(
                self.request, f'Row {line_number} skipped: {reason}.'
            )
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Simple stats: contacts per city chart data."""

    template_name = 'contacts/dashboard.html'

    # Doughnut slice colors matching the status badges in theme.css.
    STATUS_CHART_COLORS = {
        'new': '#2f5aa8',
        'in_progress': '#8a6d00',
        'lost': '#b3372f',
        'outdated': '#5b5f6a',
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Subquery keeps the stats scoped to contacts the user may see.
        visible_ids = visible_contacts(self.request.user).values('id')
        stats = list(
            Contact.objects.filter(id__in=visible_ids)
            .values('city')
            .annotate(total=Count('id'))
            .order_by('-total', 'city')
        )
        status_stats = list(
            Contact.objects.filter(id__in=visible_ids)
            .values('status__name')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        context['city_stats'] = stats
        context['total_contacts'] = visible_ids.count()
        # Plain dicts on purpose: the template serializes them with json_script.
        context['chart_data'] = {
            'labels': [s['city'] for s in stats],
            'data': [s['total'] for s in stats],
        }
        context['status_chart_data'] = {
            'labels': [
                s['status__name'].replace('_', ' ').capitalize()
                for s in status_stats
            ],
            'data': [s['total'] for s in status_stats],
            'colors': [
                self.STATUS_CHART_COLORS.get(s['status__name'], '#5b5f6a')
                for s in status_stats
            ],
        }
        return context


class WeatherView(LoginRequiredMixin, View):
    """JSON endpoint for one city. Used by weather.js after page load."""

    def get(self, request):
        city = request.GET.get('city', '').strip()
        if not city:
            return JsonResponse({'error': 'Missing city.'}, status=400)
        try:
            weather = get_city_weather(city)
        except Exception:
            return JsonResponse(
                {'error': 'Weather provider is unavailable.'}, status=502
            )
        if weather is None:
            return JsonResponse({'error': 'City not found.'}, status=404)
        return JsonResponse({'city': city, **weather})


class ContactExportView(LoginRequiredMixin, View):
    """Download the current (filtered) list as .CSV."""

    def get(self, request):
        import csv

        from django.http import HttpResponse

        contacts = filter_contacts(request.GET, request.user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
        # BOM so Excel shows diacritics correctly.
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(
            ['first_name', 'last_name', 'phone', 'email', 'city', 'status', 'created_at']
        )
        for contact in contacts:
            writer.writerow(
                [
                    contact.first_name,
                    contact.last_name,
                    contact.phone,
                    contact.email,
                    contact.city,
                    contact.status.name,
                    contact.created_at.isoformat(),
                ]
            )
        return response

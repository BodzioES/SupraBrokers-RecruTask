from django.contrib import admin

from .models import Contact, ContactStatus


@admin.register(ContactStatus)
class ContactStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'phone',
        'email',
        'city',
        'status',
        'owner',
        'is_shared',
        'created_at',
    )
    list_filter = ('status', 'is_shared', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'city')
    autocomplete_fields = ('status',)

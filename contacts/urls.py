from django.urls import path

from .views import (
    ContactCreateView,
    ContactDeleteView,
    ContactImportView,
    ContactListView,
    ContactUpdateView,
    DashboardView,
)

app_name = 'contacts'

urlpatterns = [
    path('', ContactListView.as_view(), name='list'),
    path('add/', ContactCreateView.as_view(), name='add'),
    path('import/', ContactImportView.as_view(), name='import'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('<int:pk>/edit/', ContactUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ContactDeleteView.as_view(), name='delete'),
]

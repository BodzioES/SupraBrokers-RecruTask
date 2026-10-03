from django.urls import path

from .views import (
    ContactCreateView,
    ContactDeleteView,
    ContactExportView,
    ContactImportView,
    ContactListView,
    ContactUpdateView,
    DashboardView,
    WeatherView,
)

app_name = 'contacts'

urlpatterns = [
    path('', ContactListView.as_view(), name='list'),
    path('add/', ContactCreateView.as_view(), name='add'),
    path('import/', ContactImportView.as_view(), name='import'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('weather/', WeatherView.as_view(), name='weather'),
    path('export/', ContactExportView.as_view(), name='export'),
    path('<int:pk>/edit/', ContactUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ContactDeleteView.as_view(), name='delete'),
]

from django.urls import path

from .views import (
    ContactCreateView,
    ContactDeleteView,
    ContactListView,
    ContactUpdateView,
)

app_name = 'contacts'

urlpatterns = [
    path('', ContactListView.as_view(), name='list'),
    path('add/', ContactCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', ContactUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ContactDeleteView.as_view(), name='delete'),
]

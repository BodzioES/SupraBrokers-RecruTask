from django.urls import path

from .views import HomeView

app_name = 'contacts'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]

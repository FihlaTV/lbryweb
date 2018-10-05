from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path('/login', auth_views.LoginView.as_view(), name='login'),
    path('/logout', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout')
]

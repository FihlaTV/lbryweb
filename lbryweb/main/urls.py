from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    path('', views.MainView.as_view(), name='main'),
    path('api_proxy/', csrf_exempt(views.APIProxyView.as_view()), name='api_proxy'),
    path('app/', views.AppView.as_view(), name='app'),
]

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    path(
        'content/',
        csrf_exempt(views.ContentPublishView.as_view()),
        name='publish'),
    path('content/<account_id>/<uri>', views.ContentView.as_view(), name='content'),
    path(
        'content/<account_id>/outpoints/<outpoint>/<file_name>',
        views.ContentOutpointsView.as_view(),
        name='content_outpoints'),
]

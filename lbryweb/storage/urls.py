from django.urls import path

from . import views


urlpatterns = [
    path('content/<account_id>/<uri>', views.ContentView.as_view(), name='content'),
    path(
        'content/<account_id>/outpoints/<outpoint>/<file_name>',
        views.ContentOutpointsView.as_view(),
        name='content_outpoints'),
]

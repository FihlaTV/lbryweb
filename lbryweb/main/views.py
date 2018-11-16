import json
import logging

from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest

from daemon import api


logger = logging.getLogger(__name__)


class MainView(TemplateView):
    template_name = 'main.html'


class APIProxyView(TemplateView):
    template_name = 'app.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_bound:
            return redirect('/')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        A view for proxying web app requests to internal daemon instance
        """
        try:
            parsed_data = json.loads(request.body)
        except json.JSONDecodeError as exc:
            logger.error('Exception while decoding client json: %s', exc)
            return HttpResponseBadRequest('Malformed JSON')
        if request.user.is_authenticated:
            api_client = api.API(account_id=request.user.account_id)
        else:
            api_client = api.API()
        try:
            response, _ = api_client.proxy(parsed_data)
        except Exception as exc:
            logger.error('Exception while proxying request (%s): %s', parsed_data, exc)
            return HttpResponseBadRequest(f'Proxy exception: {exc}')
        return JsonResponse(response)

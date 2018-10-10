import json

from django.views.generic import TemplateView
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest

from daemon import api


class MainView(TemplateView):
    template_name = 'main.html'

    def post(self, request, *args, **kwargs):
        """
        A view for proxying web app requests to internal daemon instance
        """
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        assert request.user.is_bound
        try:
            parsed_data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Malformed JSON')
        api_client = api.API(account_id=request.user.account_id)
        try:
            response, _ = api_client.proxy(parsed_data)
        except Exception as exc:
            return HttpResponseBadRequest(f'Proxy exception: {exc}')
        return JsonResponse(response)

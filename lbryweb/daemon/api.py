import logging
import hashlib
import copy

import requests
from django.conf import settings

from . import exceptions, signals


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class API:
    """
    Class for talking to lbrynet daemon.

    Two modes of operation:

    1. `call` — perform internal request to the daemon (account creation etc)
    2. `proxy` — augment web app request and forward it to the daemon, wait for the answer,
        augment it and send it back.
    """
    url = settings.LBRY_DAEMON

    def __init__(self, account_id=None):
        """
        Supply account_id if you need to `proxy` requests,
        omit it if only internal `call`s will be performed.
        """
        self.account_id = account_id

    def _extract_response_data(self, response):
        json = response.json()
        error = json.get('error')
        if error:
            if "Couldn't find account" in error['message']:
                raise exceptions.AccountNotFound
            else:
                raise exceptions.DaemonException(error['message'])
        return json

    def call(self, method, **kwargs):
        logger.debug('Sending request to lbrynet: %s(%s)', method, kwargs)
        response = requests.post(self.url, json={'method': method, 'params': kwargs})
        response_result = self._extract_response_data(response)['result']
        logger.debug('Got response from lbrynet: [%s] %s', response.status_code, response_result)
        return response_result

    def proxy(self, request):
        assert self.account_id
        logger.debug('Proxying request to lbrynet: %s(%s)', request['method'], request['params'])

        request_processors = {
            'get': self._augment_get_request
        }
        response_processors = {
            'get': self._augment_get_response
        }
        post_handlers = {
            'get': self._post_get_response
        }

        request_processor = request_processors.get(request['method'], self._augment_any_request)
        augmented_request = request_processor(copy.deepcopy(request))

        response = requests.post(self.url, json=augmented_request)
        response_data = self._extract_response_data(response)
        logger.debug(
            'Got response from lbrynet for proxied request: [%s] %s',
            response.status_code, response_data)

        response_processor = response_processors.get(request['method'], self._augment_any_response)
        augmented_response = response_processor(copy.deepcopy(response_data), request)

        post_handler = post_handlers.get(request['method'])
        if post_handler:
            post_handler(
                request=request, augmented_request=augmented_request,
                response=response_data, augmented_response=augmented_response)
        return augmented_response, response_data

    def _augment_any_request(self, request):
        return request

    def _augment_get_request(self, request):
        """
        Suggest a download path to the lbrynet daemon that is unique and user account-specific.
        """
        file_hash = hashlib.sha1('{account_id}{what}{settings.SECRET_KEY}'.encode('utf-8')).hexdigest()
        request['params']['file_name'] = f'{self.account_id}___{file_hash}'
        return request

    def _augment_any_response(self, response):
        return response

    def _augment_get_response(self, response, request):
        """
        Replace real download path (that resides somewhere on daemon's machine) with a http location
        at which this content will be served to web client.
        """
        download_url = (
            f'{settings.LBRY_CONTENT_URL}'
            f'{self.account_id}/'
            f'{request["params"]["uri"]}'
        )
        response['result']['download_path'] = download_url
        return response

    def _post_get_response(self, request, augmented_request, response, **kwargs):
        signals.download_started.send(
            sender=self, account_id=self.account_id, file_name=response['result']['file_name'],
            lbrynet_data=response['result'], uri=request["params"]["uri"])

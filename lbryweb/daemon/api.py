import logging
import hashlib
import copy
import re

import requests
from django.conf import settings

from . import exceptions, signals
from .profiling import Profiler


logger = logging.getLogger(__name__)


ACCOUNT_SPECIFIC_METHODS = re.compile(
    r'^(wallet)|(account)|(address)|(transaction)_.+$'
)


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
        Supply account_id if you need to perform `proxy` and `publish` requests,
        omit it if only internal `call`s will be performed.
        """
        self.account_id = account_id
        self.profiler = Profiler()

    def validate_account(self):
        if not self.account_id:
            raise exceptions.AccountMissing('Account ID is required for this type of request')

    def _extract_response_data(self, method, response):
        json = response.json()
        error = json.get('error')
        if error:
            self.profiler.error(method)
            if "Couldn't find account" in error['message']:
                raise exceptions.AccountNotFound
            else:
                raise exceptions.DaemonException(error['message'])
        return json

    def call(self, method, get_result=True, **kwargs):
        logger.debug('Sending request to lbrynet: %s(%s)', method, kwargs)
        self.profiler.start(method)
        response = requests.post(self.url, json={'method': method, 'params': kwargs})
        if get_result:
            response_result = self._extract_response_data(method, response)['result']
            logger.debug(
                'Got response from lbrynet: [%s] %s',
                response.status_code,
                response_result)
        else:
            response_result = self._extract_response_data(method, response)
            logger.debug(
                'Got response from lbrynet: [%s] %s',
                response.status_code,
                response_result['result'])
        self.profiler.end(method)
        return response_result

    def publish(self, file_path, client_payload):
        client_payload['params']['file_path'] = file_path
        daemon_response = self.call('publish', get_result=False, account_id=self.account_id, **client_payload['params'])
        return daemon_response

    def proxy(self, request):
        request_processors = {
            'get': self._augment_get_request
        }
        response_processors = {
            'get': self._augment_get_response,
            'file_list': self._augment_file_list_response,
        }
        post_handlers = {
            'get': self._post_get_response
        }

        self.profiler.start(request['method'])
        request_processor = request_processors.get(request['method'], self._augment_any_request)
        augmented_request = request_processor(copy.deepcopy(request))

        if augmented_request == request:
            logger.debug(
                'Proxying request to lbrynet: %s(%s)',
                request['method'], request.get('params', ''))
        else:
            logger.debug(
                'Proxying request to lbrynet: %s(%s) -> (%s)',
                request['method'], request.get('params', ''), augmented_request.get('params', ''))
        response = requests.post(self.url, json=augmented_request)
        response_data = self._extract_response_data(request['method'], response)
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

        self.profiler.end(request['method'])
        logger.debug(
            'Returning augmented for proxied request: %s', augmented_response)
        return augmented_response, response_data

    ### Requests

    def _augment_any_request(self, request):
        method = request['method']
        if ACCOUNT_SPECIFIC_METHODS.match(method):
            request = self._attach_account_id(request)
        return request

    def _augment_get_request(self, request):
        """
        Suggest a download path to the lbrynet daemon that is unique and user account-specific.
        """
        self.validate_account()
        # uri = request['params']['uri']
        # file_hash = hashlib.sha1('{account_id}{uri}{settings.SECRET_KEY}'.encode('utf-8')).hexdigest()
        # request['params']['file_name'] = f'{self.account_id}___{uri}___{file_hash}'
        return request

    def _attach_account_id(self, request):
        self.validate_account()
        request.setdefault('params', {})['account_id'] = self.account_id
        return request

    ### Responses

    def _augment_any_response(self, response, request):
        return response

    def _augment_get_response(self, response, request):
        """
        Replace real download path (that resides somewhere on daemon's machine) with a http location
        at which this content will be served to web client.
        """
        self.validate_account()
        download_url = (
            f'{settings.LBRY_CONTENT_URL}'
            f'{self.account_id}/'
            f'{request["params"]["uri"]}'
        )
        response['result']['download_path'] = download_url
        return response

    def _augment_file_list_response(self, response, request):
        """
        Replace real download path (that resides somewhere on daemon's machine) with a http location
        at which this content will be served to web client.
        """
        self.validate_account()
        for file_index, file_item in enumerate(response['result']):
            download_url = (
                f'{settings.LBRY_CONTENT_URL}'
                f'{self.account_id}/outpoints/'
                f'{file_item["outpoint"]}/{file_item["file_name"]}'
            )
            response['result'][file_index]['download_path'] = download_url
        return response

    def _post_get_response(self, request, augmented_request, response, **kwargs):
        self.validate_account()
        signals.download_started.send(
            sender=self, account_id=self.account_id, file_name=response['result']['file_name'],
            lbrynet_data=response['result'], uri=request["params"]["uri"])

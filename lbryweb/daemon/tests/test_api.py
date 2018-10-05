import json
import hashlib
from unittest import mock
from contextlib import contextmanager

import responses
from django.test import TestCase
from django.conf import settings

from .. import signals
from ..api import API
from .. import exceptions


@contextmanager
def assertSignalSent(signal, sender=mock.ANY, **kwargs):
    """Assert signal was sent with given parameters.

    Example:
    >>> with assertSignalSent(signal, sender=ModelClass, instance=obj):
    ...    do_something()
    """
    handler = mock.Mock()
    signal.connect(handler)
    try:
        yield handler
    finally:
        handler.assert_called_with(signal=signal, sender=sender, **kwargs)
        signal.disconnect(handler)


class APITest(TestCase):

    @responses.activate
    def test_error_response(self):
        api = API()
        responses.add(
            responses.POST, api.url,
            body=json.dumps({
                'error': {'code': -32700, 'data': [],
                'message': 'Parse Error. Data is not valid JSON.'}, 'id': None, 'jsonrpc': '2.0'
            }), status=200, content_type='application/json')
        with self.assertRaisesMessage(exceptions.DaemonException, 'Parse Error. Data is not valid JSON.'):
            api.call('account_create', account_name='test')

    @responses.activate
    def test_proxy_get(self):
        responses.add(
            responses.POST, API.url, body=DAEMON_GET_RESPONSE, status=200, content_type='application/json')

        account_id = 'abc'
        uri = 'what'
        file_hash = hashlib.sha1('{account_id}{what}{settings.SECRET_KEY}'.encode('utf-8')).hexdigest()
        file_name = f'{account_id}___{file_hash}'
        api = API(account_id=account_id)
        web_client_payload = {'method' :'get', 'params': {'uri': uri}}
        augmented_payload = {'method' :'get', 'params': {'uri': uri, 'file_name': file_name}}

        with assertSignalSent(
            signals.download_started, uri=uri, file_name=mock.ANY, account_id=account_id,
            lbrynet_data=json.loads(DAEMON_GET_RESPONSE)['result']) as mock_handler:
            augmented_response, actual_response = api.proxy(web_client_payload)
            # Check that we feed the signal whatever daemon actually returned us
            # because file might have already been downloaded under a different user
            self.assertEqual(
                mock_handler.mock_calls[0][2]['file_name'],
                actual_response['result']['file_name']
            )
        # Detect a get request and suggest an amended file name to the daemon as a download location
        # which contains account_id and some hash to avoid collisions
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            augmented_payload
        )
        self.assertEqual(
            augmented_response['result']['download_path'],
            f'{settings.LBRY_CONTENT_URL}{account_id}/{uri}'
        )
        self.assertEqual(
            actual_response,
            json.loads(DAEMON_GET_RESPONSE)
        )

    # def test_proxy_account_balance(self):
    #     account_id = 'abc'
    #     proxy = Proxy(account_id=account_id)
    #     payload = {'method' :'account_balance', 'params': {'account_id': account_id}}
    #     result = proxy.call(payload)
    #     self.assertEqual(result, '25.6')


DAEMON_GET_RESPONSE = """
{
  "id": null,
  "jsonrpc": "2.0",
  "result": {
    "blobs_completed": 1,
    "blobs_in_stream": 76,
    "channel_claim_id": null,
    "channel_name": null,
    "claim_id": "6769855a9aa43b67086f9ff3c1a5bacb5698a27a",
    "claim_name": "what",
    "completed": false,
    "download_directory": "/lbry/download",
    "download_path": "/lbry/download/test",
    "file_name": "test",
    "key": "0edc1705489d7a2b2bcad3fea7e5ce92",
    "metadata": {
      "author": "Samuel Bryan",
      "description": "What is LBRY? An introduction with Alex Tabarrok",
      "language": "en",
      "license": "LBRY inc",
      "licenseUrl": "",
      "nsfw": false,
      "preview": "",
      "thumbnail": "https://s3.amazonaws.com/files.lbry.io/logo.png",
      "title": "What is LBRY?",
      "version": "_0_1_0"
    },
    "mime_type": null,
    "nout": 0,
    "outpoint": "6c71c02c4990ce0590f6888a77ad11f1ae45486f6a4c56d5013954ee8f6356bc:0",
    "points_paid": 0.0,
    "sd_hash": "d5169241150022f996fa7cd6a9a1c421937276a3275eb912790bd07ba7aec1fac5fd45431d226b8fb402691e79aeb24b",
    "status": "running",
    "stopped": false,
    "stream_hash": "9f41e37b1ea706d1b431a65f634b89c5aadefb106280da3661e4d565d47bc938a345755cafb2af807bcfc9fbde3306e3",
    "stream_name": "LBRY100.mp4",
    "suggested_file_name": "LBRY100.mp4",
    "total_bytes": 158433904,
    "txid": "6c71c02c4990ce0590f6888a77ad11f1ae45486f6a4c56d5013954ee8f6356bc",
    "written_bytes": 0
  }
}
"""

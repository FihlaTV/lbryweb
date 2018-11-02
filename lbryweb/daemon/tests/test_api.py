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
        api = API(account_id=account_id)
        web_client_payload = {'method' :'get', 'params': {'uri': uri}}
        augmented_payload = web_client_payload
        # augmented_payload = {'method' :'get', 'params': {'uri': uri, 'file_name': file_name}}

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
        self.assertTrue(augmented_response['result']['download_path'].startswith('http://'))
        self.assertEqual(
            actual_response,
            json.loads(DAEMON_GET_RESPONSE)
        )

    @responses.activate
    def test_proxy_file_list_by_outpoint(self):
        responses.add(
            responses.POST, API.url,
            body=DAEMON_FILE_LIST_RESPONSE, status=200, content_type='application/json')

        account_id = 'abc'
        outpoint = '09fb2ae827bcd8f676a7d570120ae016cacf805efc9a399d2873859f492ba500:0'
        api = API(account_id=account_id)
        web_client_payload = {
            'method' :'file_list',
            'params': {
                'outpoint': '09fb2ae827bcd8f676a7d570120ae016cacf805efc9a399d2873859f492ba500:0',
                'full_status': True
            }
        }
        augmented_response, actual_response = api.proxy(web_client_payload)
        self.assertEqual(
            augmented_response['result'][0]['download_path'],
            f'{settings.LBRY_CONTENT_URL}{account_id}/outpoints/{outpoint}/{augmented_response["result"][0]["file_name"]}'
        )
        self.assertTrue(augmented_response['result'][0]['download_path'].startswith('http://'))
        self.assertEqual(
            actual_response,
            json.loads(DAEMON_FILE_LIST_RESPONSE)
        )

    @responses.activate
    def test_proxy_file_list(self):
        responses.add(
            responses.POST, API.url,
            body=DAEMON_FILE_LIST_RESPONSE, status=200, content_type='application/json')

        account_id = 'abc'
        api = API(account_id=account_id)
        outpoint = '09fb2ae827bcd8f676a7d570120ae016cacf805efc9a399d2873859f492ba500:0'
        web_client_payload = {
            'method' :'file_list',
            'params': {}
        }
        augmented_response, actual_response = api.proxy(web_client_payload)
        self.assertEqual(
            augmented_response['result'][0]['download_path'],
            f'{settings.LBRY_CONTENT_URL}{account_id}/outpoints/{outpoint}/{augmented_response["result"][0]["file_name"]}'
        )
        self.assertTrue(augmented_response['result'][0]['download_path'].startswith('http://'))
        self.assertEqual(
            actual_response,
            json.loads(DAEMON_FILE_LIST_RESPONSE)
        )

    @responses.activate
    def test_proxy_status(self):
        responses.add(
            responses.POST, API.url, body=DAEMON_STATUS_RESPONSE, status=200, content_type='application/json')

        api = API(account_id=None)
        web_client_payload = {'jsonrpc': '2.0', 'method': 'status', 'params': {}, 'id': 123}
        augmented_payload = web_client_payload
        augmented_response, actual_response = api.proxy(web_client_payload)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            augmented_payload
        )
        self.assertEqual(
            actual_response,
            json.loads(DAEMON_STATUS_RESPONSE)
        )
        self.assertEqual(augmented_response, actual_response)

    @responses.activate
    def test_proxy_account_balance(self):
        responses.add(
            responses.POST, API.url, body=DAEMON_ACCOUNT_RESPONSE, status=200, content_type='application/json')
        account_id = 'abc'
        api = API(account_id=account_id)
        web_client_payload = {'method' :'account_balance'}
        augmented_payload = {'method' :'account_balance', 'params': {'account_id': account_id}}
        api.proxy(web_client_payload)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            augmented_payload
        )


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

DAEMON_ACCOUNT_RESPONSE = """
{
  "id": null,
  "jsonrpc": "2.0",
  "result": 0.0
}
"""

DAEMON_STATUS_RESPONSE = """
{
  "id": 1540362499887,
  "jsonrpc": "2.0",
  "result": {
    "blob_manager": {
      "finished_blobs": 77
    },
    "connection_status": {
      "code": "connected",
      "message": "No connection problems detected"
    },
    "dht": {
      "node_id": "844951b80672ea9c95660b2fff1f5daeb5d5fe943065349a60166f83fcadba03977c88b723dd9988a6870f119db8a35c",
      "peers_in_routing_table": 11
    },
    "file_manager": {
      "managed_files": 1
    },
    "hash_announcer": {
      "announce_queue_size": 0
    },
    "installation_id": "7Cz1yhpCDxfxxHC9yJXDwE9KuY594gyvBU5mWw2FFru4pgP4MF4a2m9ZFrLQ8Sah95",
    "is_first_run": false,
    "is_running": true,
    "skipped_components": [
      "reflector"
    ],
    "startup_status": {
      "blob_manager": true,
      "blockchain_headers": true,
      "database": true,
      "dht": true,
      "exchange_rate_manager": true,
      "file_manager": true,
      "hash_announcer": true,
      "payment_rate_manager": true,
      "peer_protocol_server": true,
      "rate_limiter": true,
      "stream_identifier": true,
      "upnp": true,
      "wallet": true
    },
    "wallet": {
      "best_blockhash": "",
      "blocks": 457992,
      "blocks_behind": 0,
      "is_encrypted": false,
      "is_locked": false
    }
  }
}
"""

DAEMON_FILE_LIST_RESPONSE = """
{
    "id": 1540367573006,
    "jsonrpc": "2.0",
    "result": [
        {
            "blobs_completed": 2,
            "blobs_in_stream": 473,
            "channel_claim_id": null,
            "channel_name": null,
            "claim_id": "ca0477e98923d4da7829136a20f34a4e2e5db413",
            "claim_name": "they-got-me-to-buy-a-ps4-spiderman",
            "completed": false,
            "download_directory": "/storage/download",
            "download_path": "/storage/download/spiderman-ps4-prt-1-the-start.mp4",
            "file_name": "spiderman-ps4-prt-1-the-start.mp4",
            "key": "6515032937a5920ee89f5f174af6179d",
            "metadata": {
                "author": "Gunslinger Media",
                "description": "https: //www.youtube.com/watch?v=QmmI4npNsak",
                "language": "en",
                "license": "Copyrighted (contact author)",
                "licenseUrl": "",
                "nsfw": false,
                "preview": "",
                "thumbnail": "https://berk.ninja/thumbnails/QmmI4npNsak",
                "title": "They got me to buy a PS4 (Spiderman Weekend)",
                "version": "_0_1_0"
            },
            "mime_type": null,
            "nout": 0,
            "outpoint": "09fb2ae827bcd8f676a7d570120ae016cacf805efc9a399d2873859f492ba500:0",
            "points_paid": "0.0",
            "sd_hash": "24cdf5a7b485e2340aae4dd3f4e61eeb55ba0e162e6087f71aa4ace1f4a228a9b5e1f8dcc719975bd33283426a2907cb",
            "status": "running",
            "stopped": false,
            "stream_hash": "e66f8ff716f7b32331fca882830b950849ba778b8b652128bad60ba0b27afbfa528f460a00cf989cdc94cae82ced6c7e",
            "stream_name": "they-got-me-to-buy-a-ps4.mp4",
            "suggested_file_name": "they-got-me-to-buy-a-ps4.mp4",
            "total_bytes": 990411408,
            "txid": "09fb2ae827bcd8f676a7d570120ae016cacf805efc9a399d2873859f492ba500",
            "written_bytes": 0
        }
    ]
}
"""

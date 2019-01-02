import time
import json
import hashlib
import os
from io import BytesIO
from datetime import datetime

import pytest
import responses
from django.test import TestCase
from django.urls import reverse
from django.contrib import auth
from django.conf import settings

from users.models import User
from registration.daemon_plug import Account
from daemon.api import API

from ..models import Content


class StorageViewTest(TestCase):

    def test_get(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        # while True:
        #     response = api_client.call('get', uri=uri)
        #     if response['completed']:
        #         break
        #     time.sleep(1)

        content_instance = Content.objects.get(uri=uri)
        content_response = self.client.get(reverse('content', kwargs={
            'uri': uri, 'account_id': user.account_id}))
        self.assertTrue(hasattr(content_response, 'streaming_content'))
        self.assertEqual(content_response['Content-Type'], 'video/mp4')
        self.assertEqual(
            content_response['Content-Length'],
            str(content_instance.lbrynet_data['total_bytes'])
        )

        # Repeated queries do not produce duplicate Content instances
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Content.objects.filter(outpoint=content_instance.outpoint).count(),
            1
        )

    def test_get_by_outpoint(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        # while True:
        #     response = api_client.call('get', uri=uri)
        #     if response['completed']:
        #         break
        #     time.sleep(1)

        content_instance = Content.objects.get(uri=uri)
        content_response = self.client.get(
            reverse('content_outpoints', kwargs={
                'outpoint': response_data['result']['outpoint'],
                'file_name': 'what.mp4', 'account_id': user.account_id
        }))
        self.assertTrue(hasattr(content_response, 'streaming_content'))
        self.assertEqual(content_response['Content-Type'], 'video/mp4')
        self.assertEqual(
            content_response['Content-Length'],
            str(content_instance.lbrynet_data['total_bytes'])
        )
        self.assertEqual(
            content_response['Accept-Ranges'], 'bytes'
        )

    def test_get_by_outpoint_with_range(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        content_instance = Content.objects.get(uri=uri)
        last_byte = content_instance.lbrynet_data['total_bytes'] - 1

        content_response = self.client.get(
            reverse('content_outpoints', kwargs={
                'outpoint': response_data['result']['outpoint'],
                'file_name': 'what.mp4', 'account_id': user.account_id
        }), HTTP_RANGE='bytes=0-')
        binary_content = b''.join(content_response.streaming_content)
        # self.assertEqual(len(binary_content), content_instance.get_physical_file().stat().st_size)
        self.assertEqual(len(binary_content), content_instance.lbrynet_data['total_bytes'])
        self.assertEqual(content_response['Content-Type'], 'video/mp4')
        self.assertEqual(
            content_response['Content-Length'],
            str(content_instance.lbrynet_data['total_bytes'])
        )
        self.assertEqual(
            content_response['Content-Range'],
            f"bytes 0-{last_byte}/{content_instance.lbrynet_data['total_bytes']}"
        )
        self.assertEqual(content_response['Accept-Ranges'], 'bytes')
        self.assertEqual(content_response.status_code, 206)

        content_response = self.client.get(
            reverse('content_outpoints', kwargs={
                'outpoint': response_data['result']['outpoint'],
                'file_name': 'what.mp4', 'account_id': user.account_id
        }), HTTP_RANGE='bytes=100-10000')
        self.assertTrue(hasattr(content_response, 'streaming_content'))
        self.assertEqual(content_response['Content-Type'], 'video/mp4')
        self.assertEqual(
            content_response['Content-Length'],
            '9901'
        )
        self.assertEqual(
            content_response['Content-Range'],
            f"bytes 100-10000/{content_instance.lbrynet_data['total_bytes']}"
        )
        self.assertEqual(content_response['Accept-Ranges'], 'bytes')
        self.assertEqual(content_response.status_code, 206)

        content_response = self.client.get(
            reverse('content_outpoints', kwargs={
                'outpoint': response_data['result']['outpoint'],
                'file_name': 'what.mp4', 'account_id': user.account_id
        }), HTTP_RANGE='bytes=5000-')
        self.assertTrue(hasattr(content_response, 'streaming_content'))
        self.assertEqual(content_response['Content-Type'], 'video/mp4')
        self.assertEqual(
            content_response['Content-Length'],
            str(content_instance.lbrynet_data['total_bytes'] - 5000)
        )
        self.assertEqual(
            content_response['Content-Range'],
            f"bytes 5000-{last_byte}/{content_instance.lbrynet_data['total_bytes']}"
        )
        self.assertEqual(content_response['Accept-Ranges'], 'bytes')
        self.assertEqual(content_response.status_code, 206)

    @pytest.mark.xfail
    def test_get_other_users_content(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        owner = User.objects.create(username='test@lbry.io')
        account = Account(user=owner)
        account.register()
        self.client.force_login(owner)
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        user = User.objects.create(username='test2@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.get(reverse('content', kwargs={
            'uri': uri, 'account_id': user.account_id}))
        self.assertEqual(response.status_code, 404)

    def test_get_404(self):
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.get(reverse('content', kwargs={
            'uri': 'asdjsaklfjlksdjflksdhglsd', 'account_id': user.account_id}))
        self.assertEqual(response.status_code, 404)

    def test_get_unauthorized(self):
        response = self.client.get(reverse('content', kwargs={
            'uri': 'what', 'account_id': '123'}))
        self.assertEqual(response.status_code, 404)


class PublishViewTest(TestCase):
    maxDiff = None

    def test_post(self):
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)

        with responses.RequestsMock() as responses_mock:
            responses_mock.add(
                responses.POST, API.url,
                body=DAEMON_PUBLISH_RESPONSE, status=200, content_type='application/json')

            faux_file = BytesIO(b'He\'s just a poor boy from a poor family')
            faux_file.name = 'publishing_test.txt'
            data = {
                'file': faux_file,
                'json_payload': """{
                    "jsonrpc": "2.0",
                    "method": "publish",
                    "params": {
                        "name": "DSC0097squarejpg",
                        "channel_id": "",
                        "bid": "0.10000000",
                        "metadata": {
                            "title": "lwt1331",
                            "nsfw": false,
                            "license": "None",
                            "licenseUrl": "",
                            "language": "en",
                            "thumbnail": ""
                        },
                        "file_path": "__POST_FILE__"
                    },
                    "id": 1545152100250
                }"""
            }
            response = self.client.post(reverse('publish'), data)
            self.assertEqual(response.status_code, 200, response.content)
            daemon_request_payload = json.loads(responses_mock.calls[0].request.body)

            self.assertEqual(daemon_request_payload['params']['account_id'], user.account_id)
            filename_hash_bits = ':'.join([
                user.account_id,
                settings.SECRET_KEY,
                'publishing_test.txt'
            ]).encode('utf-8')
            filename = hashlib.sha1(filename_hash_bits).hexdigest() + '_' + 'publishing_test.txt'
            self.assertEqual(
                daemon_request_payload['params']['file_path'],
                os.path.join(
                    settings.LBRY_PUBLISH_FEED,
                    'account_' + str(user.account_id),
                    filename),
            )
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertEqual(response_data, json.loads(DAEMON_PUBLISH_RESPONSE))


DAEMON_PUBLISH_RESPONSE = """
{
  "id": 1543922089251,
  "jsonrpc": "2.0",
  "result": {
    "claim_address": "bFJi72E23gmTfJU7Ce9fFZk956XP7ZGYmZ",
    "claim_id": "02ce79ed282abe180adb0d31a8c8eac3b02ab1b7",
    "fee": 0.012,
    "nout": 0,
    "tx": "0100000001717513921ea6bff81fb9f2ff34c62bac78e5ffd4f4234f51954e5256d50bb668010000006a47304402205b3d352cfb7fb0d9e8914dad5524c39679e8eea2c0be55a634a2b382e94395a50220680cb134a61bfdac24966035dcd693b98a220e81b4a991fab34adcee65955f0a01210258a13883466f4b52cdc8ca6771af0840ffbaac1abddc3ae8e193a9b09d1bc211ffffffff028096980000000000adb50668656c6c6f324c88080110011a81010801122b080410011a0474657374220f68656c6c6f202a2a776f726c642a2a2a0032044e6f6e6538004a0052005a001a50080110011a30120d4a444ccc6666cec6fb8b3e7db6089a6420b55fbc385fba2b647441fc27c8bfb818867b7ac44eff7837ea2b72533622186170706c69636174696f6e2f6f637465742d73747265616d6d7576a9141c43308e0990af81bb9e68849d21aca19e8c14db88acdc52221d000000001976a9145bc94f19c4361bc77a7174828a0683dfc80d444a88ac00000000",
    "txid": "42e05059c7953b32a57553e2d86eb8db3e05313ef211e53e36647429de6d1240",
    "value": "080110011a81010801122b080410011a0474657374220f68656c6c6f202a2a776f726c642a2a2a0032044e6f6e6538004a0052005a001a50080110011a30120d4a444ccc6666cec6fb8b3e7db6089a6420b55fbc385fba2b647441fc27c8bfb818867b7ac44eff7837ea2b72533622186170706c69636174696f6e2f6f637465742d73747265616d"
  }
}
"""

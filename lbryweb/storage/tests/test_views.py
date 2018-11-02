import time
import json

import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib import auth

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

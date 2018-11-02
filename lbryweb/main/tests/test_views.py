import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib import auth

from daemon.api import API
from users.models import User
from registration.daemon_plug import Account


class MainViewTest(TestCase):

    def test_get_authenticated(self):
        valid_data = {'email': 'test@lbry.io', 'password1': 'qwerty', 'password2': 'qwerty'}
        self.client.post(reverse('registration'), valid_data)
        response = self.client.get(reverse('main'))
        account = Account(user=User.objects.get(username='test@lbry.io'))
        content = response.content.decode('utf-8')
        self.assertIn(account.get_details()['id'], content)
        self.assertIn('test@lbry.io', content)
        self.assertIn(reverse('logout'), content)
        # Cleanup
        account.unregister()

    def test_get(self):
        response = self.client.get(reverse('main'))
        content = response.content.decode('utf-8')
        self.assertIn(reverse('login'), content)
        self.assertIn(reverse('registration'), content)


class APIProxyViewTest(TestCase):

    def test_post_get_anonymous(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_post_get_authenticated(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        fake_daemon_response = {
            "id": None,
            "jsonrpc": "2.0",
            "result": {
                "blobs_completed": 1,
            }
        }
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        with patch('daemon.api.API') as mock_proxy:
            instance = mock_proxy.return_value
            instance.proxy.return_value = (fake_daemon_response, None)
            response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
            mock_proxy.assert_called_with(account_id=user.account_id)
            instance.proxy.assert_called_with(query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content), fake_daemon_response)

    def test_post_get_with_broken_user(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        fake_daemon_response = {
            "id": None,
            "jsonrpc": "2.0",
            "result": {
                "blobs_completed": 1,
            }
        }
        user = User.objects.create(username='test@lbry.io')
        self.client.force_login(user)
        response = self.client.post(reverse('api_proxy'), query, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_post_get_authenticated_with_header(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        fake_daemon_response = {
            "id": None,
            "jsonrpc": "2.0",
            "result": {
                "blobs_completed": 1,
            }
        }
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        user.refresh_from_db()
        with patch('daemon.api.API') as mock_proxy:
            instance = mock_proxy.return_value
            instance.proxy.return_value = (fake_daemon_response, None)
            response = self.client.post(
                reverse('api_proxy'), query, content_type='application/json',
                HTTP_X_LBRYNET_ACCOUNT_ID=user.account_id)
            mock_proxy.assert_called_with(account_id=user.account_id)
            instance.proxy.assert_called_with(query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content), fake_daemon_response)

    def test_post_get_malformed(self):
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        self.client.force_login(user)
        response = self.client.post(reverse('api_proxy'), 'zzz{}', content_type='application/json')
        self.assertEqual(response.status_code, 400, response.content)
        response = self.client.post(reverse('api_proxy'), '{}', content_type='application/json')
        self.assertEqual(response.status_code, 400, response.content)

    def test_post_real(self):
        uri = 'what'
        query = {'method' :'get', 'params': {'uri': uri}}
        user = User.objects.create(username='test@lbry.io')
        account = Account(user=user)
        account.register()
        user.refresh_from_db()
        response = self.client.post(
            reverse('api_proxy'), query, content_type='application/json',
            HTTP_X_LBRYNET_ACCOUNT_ID=user.account_id)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['result']['download_path'].startswith('http://'))

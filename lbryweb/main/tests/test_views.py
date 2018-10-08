from django.test import TestCase
from django.urls import reverse
from django.contrib import auth

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

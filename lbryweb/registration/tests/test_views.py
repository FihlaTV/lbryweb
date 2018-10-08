from django.test import TestCase
from django.urls import reverse
from django.contrib import auth

from users.models import User
from ..daemon_plug import Account


class RegistrationViewTest(TestCase):

    def test_get(self):
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_get_for_registered_user(self):
        self.client.force_login(User.objects.create(username='test@lbry.io'))
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 403)

    def test_post_invalid_data(self):
        missing_fields = {'email': 'test@lbry.io'}
        response = self.client.post(reverse('registration'), missing_fields)
        self.assertFormError(response, 'form', 'password1', 'This field is required.')
        self.assertFormError(response, 'form', 'password2', 'This field is required.')

        invalid_fields = {'email': 'test@asdfsadas', 'password1': 'qqq', 'password2': 'qqq'}
        response = self.client.post(reverse('registration'), invalid_fields)
        self.assertFormError(response, 'form', 'email', 'Enter a valid email address.')

        invalid_fields = {'email': 'test@asdfsadas', 'password1': 'qqq1', 'password2': 'qqq2'}
        response = self.client.post(reverse('registration'), invalid_fields)
        self.assertFormError(response, 'form', 'password2', 'Make sure the passwords match.')

    def test_post_email_taken(self):
        User.objects.create(username='test@lbry.io')
        valid_data = {'email': 'test@lbry.io', 'password1': 'qwerty', 'password2': 'qwerty'}
        response = self.client.post(reverse('registration'), valid_data)
        self.assertFormError(response, 'form', 'email', 'Enter an email that doesn\'t belong to an existing user.')

    def test_post(self):
        valid_data = {'email': 'test@lbry.io', 'password1': 'qwerty', 'password2': 'qwerty'}
        response = self.client.post(reverse('registration'), valid_data)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, valid_data['email'])
        self.assertEqual(user.email, valid_data['email'])
        self.assertTrue(user.is_bound)
        account = Account(user=user)
        self.assertEqual(account.get_details()['id'], user.account_id)
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'test@lbry.io', 'password': 'qwerty'})
        self.assertEqual(response.status_code, 302)
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)
        # Cleanup
        account.unregister()

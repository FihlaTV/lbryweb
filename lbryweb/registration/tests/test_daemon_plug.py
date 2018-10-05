import json

import responses
from django.test import TestCase
from django.conf import settings

from daemon.api import API
from daemon import exceptions
from .. import daemon_plug
from ..daemon_plug import Account, AccountAlreadyExists
from users.models import User


class RegistratorTest(TestCase):
    purgeable_account_ids = []

    def tearDown(self):
        api = API()
        for _ in range(len(self.purgeable_account_ids)):
            account_id = self.purgeable_account_ids.pop()
            api.call('account_remove', account_id=account_id)

    def test_register(self):
        user = User.objects.create(username='test@lbry.io')
        self.assertFalse(user.is_bound)
        account = Account(user=user)
        account.register()
        user.refresh_from_db()
        self.assertTrue(user.is_bound)
        self.assertEqual(account.get_details()['id'], user.account_id)
        self.assertEqual(account.get_details()['name'], user.account_data['name'])
        self.purgeable_account_ids.append(user.account_id)

    def test_register_prevents_duplicate_register_calls(self):
        user = User.objects.create(username='test@lbry.io')
        self.assertFalse(user.is_bound)
        account = Account(user=user)
        account.register()
        with self.assertRaises(AccountAlreadyExists):
            account.register()

    def test_unregister(self):
        user = User.objects.create(username='test@lbry.io')
        self.assertFalse(user.is_bound)
        account = Account(user=user)
        account.register()
        user.refresh_from_db()
        self.assertTrue(user.is_bound)
        account_id = user.account_id
        account.unregister()
        user.refresh_from_db()
        self.assertFalse(user.is_bound)
        with self.assertRaises(exceptions.AccountNotFound):
            account.api.call('account_list', account_id=account_id)

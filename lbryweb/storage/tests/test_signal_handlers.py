from django.test import TestCase

from daemon.api import API
from users.models import User
from registration.daemon_plug import Account
from ..models import Content


class SignalHandlersTest(TestCase):

    def test_create_content_object(self):
        user = User.objects.create(username='test@lbry.io')
        account = Account(user)
        account.register()
        api = API(account_id=user.account_id)
        uri = 'what'
        download_request = {'method' :'get', 'params': {'uri': uri}}
        _, response = api.proxy(download_request)
        instance = Content.objects.get(lbrynet_data__claim_name=response['result']['claim_name'])
        self.assertEqual(instance.downloaded_by, user)
        self.assertEqual(instance.uri, uri)
        self.assertTrue(instance.get_physical_file().is_file())
        self.assertEqual(instance.outpoint, response['result']['outpoint'])

import logging

from daemon.api import API


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AccountAlreadyExists(Exception):
    pass


class Account:

    def __init__(self, user):
        self.user = user
        self.api = API()

    def register(self):
        self.user.refresh_from_db()
        if self.user.is_bound:
            raise AccountAlreadyExists
        account_data = self.api.call('account_create', account_name=self.user.username)
        assert account_data['status'] == 'created'
        self.user.account_id = account_data['id']
        self.user.account_data = account_data
        self.user.save()

    def unregister(self):
        assert self.user.is_bound
        response = self.api.call('account_remove', account_id=self.user.account_id)
        assert response['status'] == 'removed'
        self.user.account_id = ''
        self.user.account_data = None
        self.user.save()

    def get_details(self):
        assert self.user.is_bound
        return self.api.call('account_list', account_id=self.user.account_id)

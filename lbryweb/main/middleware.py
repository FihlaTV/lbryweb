import logging
from django.contrib.auth import authenticate, login
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin

from users.models import User


logger = logging.getLogger(__name__)


class LbrynetAccountMiddleware(MiddlewareMixin):
    """
    Authenticate user by X-Lbrynet-Account-Id header
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured()
        if request.user.is_authenticated:
            return
        try:
            user = User.objects.get(account_id=request.META['HTTP_X_LBRYNET_ACCOUNT_ID'])
        except (User.DoesNotExist, KeyError):
            pass
        else:
            request.user = user
            login(request, user)


class AccountIdCookieMiddleware(MiddlewareMixin):
    """
    Authenticate user by X-Lbrynet-Account-Id header
    """
    def process_response(self, request, response):
        if request.user.is_authenticated:
            if not request.user.is_bound:
                logger.warn('User %s is not bound', request.user)
            else:
                response.set_cookie('lbrynet_account_id', request.user.account_id)
        return response

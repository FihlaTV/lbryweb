from django.contrib.auth import authenticate, login
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin

from users.models import User


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

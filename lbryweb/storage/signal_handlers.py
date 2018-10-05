import logging

from django.dispatch import receiver

from daemon import signals as daemon_signals
from users.models import User
from .models import Content


logger = logging.getLogger(__name__)


@receiver(daemon_signals.download_started)
def create_content_object(sender, account_id, uri, lbrynet_data, file_name, **kwargs):
    logger.debug(
        'Creating content object for account=%s, uri=%s, claim_name=%s',
        account_id, uri, lbrynet_data['claim_name']
    )
    try:
        user = User.objects.get(account_id=account_id)
    except User.DoesNotExist:
        logger.error('User with account_id=%s not found, not saving Content object', account_id)
        return
    Content.objects.create(
        downloaded_by=user,
        claim_name=lbrynet_data['claim_name'], uri=uri, file_name=file_name,
        lbrynet_data=lbrynet_data
    )

import os
import logging
import mimetypes
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.postgres.fields import JSONField


logger = logging.getLogger(__name__)


class Content(models.Model):
    downloaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=1000)
    uri = models.CharField(max_length=1000)
    claim_name = models.CharField(max_length=1000)
    outpoint = models.CharField(max_length=1000, unique=True)
    lbrynet_data = JSONField()

    def get_physical_file(self):
        logger.debug(
            'Making Path object for %s + %s',
            settings.LBRY_DOWNLOAD_DIRECTORY,
            self.file_name)
        return Path(os.path.join(settings.LBRY_DOWNLOAD_DIRECTORY, self.file_name))

    def get_suggested_file_name(self):
        return self.lbrynet_data['suggested_file_name']

    def get_mime_type(self):
        guessed_type = mimetypes.guess_type(self.get_suggested_file_name())[0]
        if not guessed_type:
            logger.warn('Unable to guess file MIME type from "%s" filename', self.file_name)
            return 'application/octet-stream'
        else:
            return guessed_type

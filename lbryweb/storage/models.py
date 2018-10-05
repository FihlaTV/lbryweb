import os
from pathlib import Path
import logging

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
    lbrynet_data = JSONField()

    def get_file(self):
        logger.debug(
            'Making Path object for %s + %s',
            settings.LBRY_DOWNLOAD_DIRECTORY,
            self.file_name)
        print(settings.LBRY_DOWNLOAD_DIRECTORY)
        print(self.file_name)
        return Path(os.path.join(settings.LBRY_DOWNLOAD_DIRECTORY, self.file_name))

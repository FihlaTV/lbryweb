from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField


class User(AbstractUser):
    account_id = models.CharField(max_length=150, blank=True)
    account_data = JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.email = self.username
        super().save(*args, **kwargs)

    @property
    def is_bound(self):
        return bool(self.account_id)

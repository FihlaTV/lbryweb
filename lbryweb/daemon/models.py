from django.db import models
from django.contrib.postgres.fields import JSONField


class Operation(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=200)
    errored = models.BooleanField(default=False)
    meta = JSONField(blank=True, null=True)

    def __str__(self):
        if self.duration is not None:
            return f'[{self.name}] {self.duration:.4f} secs'
        else:
            return f'[{self.name}] {self.started} - ...'

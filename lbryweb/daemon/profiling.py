import logging
from django.utils import timezone

from .models import Operation


class Profiler:

    def __init__(self):
        self.timers = {}
        self.logger = logging.getLogger(__name__)

    def start(self, operation_name):
        self.timers[operation_name] = Operation.objects.create(name=operation_name)

    def _close_op(self, operation_name, errored=False):
        op_instance = self.timers[operation_name]
        now = timezone.now()
        op_instance.ended = now
        op_instance.duration = (now - op_instance.started).total_seconds()
        op_instance.errored = errored
        op_instance.save()
        del self.timers[operation_name]
        return op_instance.duration

    def end(self, operation_name):
        try:
            duration = self._close_op(operation_name)
            self.logger.info('Operation %s done in %.2f secs', operation_name, duration)
        except KeyError:
            self.logger.error('Operation %s was done but never was reported as started', operation_name)

    def error(self, operation_name):
        try:
            duration = self._close_op(operation_name, errored=True)
            self.logger.info('Operation %s errored in %.2f secs', operation_name, duration)
        except KeyError:
            self.logger.error('Operation %s has errored but never reported as started', operation_name)

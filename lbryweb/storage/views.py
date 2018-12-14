import os
import logging
import hashlib
import json
from datetime import datetime

from django.views import View
from django.shortcuts import get_object_or_404
from django.http import (
    StreamingHttpResponse, Http404, HttpResponse, HttpResponseForbidden,
    JsonResponse, HttpResponseBadRequest)
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from daemon.api import API
from . import file_utils
from .models import Content


logger = logging.getLogger(__name__)


class ContentView(View):

    def get_instance(self, request, **kwargs):
        return get_object_or_404(
            # Content.objects.filter(downloaded_by=request.user), uri=kwargs['uri'])
            Content.objects.all(), uri=kwargs['uri'])

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404()
        content_instance = self.get_instance(request, **kwargs)
        file_size = content_instance.lbrynet_data['total_bytes']
        real_file_size = content_instance.get_physical_file().stat().st_size
        if real_file_size != file_size:
            logger.warning(
                'File mismatch: %s - %s (%s bytes difference)',
                file_size, real_file_size, file_size - real_file_size
            )
        file_handle = content_instance.get_physical_file().open(mode='rb')
        file_type = content_instance.get_mime_type()
        first_byte, last_byte = file_utils.parse_range_header(
            request.META.get('HTTP_RANGE', ''), file_size)
        logger.info(
            'Requested range %s-%s out of %s (%s on disk)',
            first_byte, last_byte, file_size, real_file_size
        )
        if first_byte is not None:
            if first_byte > real_file_size:
                return HttpResponse('', status=416)
            response = StreamingHttpResponse(
                file_utils.RangeFileWrapper(file_handle, offset=first_byte, length=file_size),
                status=206, content_type=file_type
            )
            response['Content-Length'] = str(last_byte - first_byte + 1)
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        else:
            response = StreamingHttpResponse(
                file_utils.FileWrapper(file_handle),
                content_type=file_type
            )
            response['Content-Length'] = file_size
        response['Accept-Ranges'] = 'bytes'
        return response


class ContentOutpointsView(ContentView):

    def get_instance(self, request, **kwargs):
        return get_object_or_404(
            # Content.objects.filter(downloaded_by=request.user), outpoint=kwargs['outpoint'])
            Content.objects.all(), outpoint=kwargs['outpoint'])


class ContentPublishView(View):
    json_payload_field = 'json_payload'
    file_field = 'file'

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        api_client = API(request.user.account_id)
        storage = FileSystemStorage(location=os.path.join(
            settings.LBRY_PUBLISH_DIRECTORY, f'account_{request.user.account_id}'))
        try:
            uploaded_file = request.FILES[self.file_field]
            filename_hash_bits = ':'.join([
                request.user.account_id,
                str(datetime.now().timestamp()),
                settings.SECRET_KEY,
                uploaded_file.name
            ])
            final_filename = hashlib.sha1(filename_hash_bits).hexdigest() + '_' + uploaded_file.name
            file_path = storage.save(final_filename, uploaded_file)
            client_payload = json.loads(request.POST[self.json_payload_field])
            return JsonResponse(api_client.publish(file_path, client_payload))
        except KeyError as exc:
            logger.error('Exception while parsing request: %s', exc)
            return HttpResponseBadRequest(f'Proxy exception: {exc}')
        except Exception as exc:
            logger.error('Exception while processing PUBLISH request: %s', exc)
            return HttpResponseBadRequest(f'Proxy exception: {exc}')

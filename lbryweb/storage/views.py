import logging

from django.views import View
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse, Http404, HttpResponse

from . import file_utils
from .models import Content


log = logging.getLogger(__name__)


class ContentView(View):

    def get_instance(self, request, **kwargs):
        return get_object_or_404(
            # Content.objects.filter(downloaded_by=request.user), uri=kwargs['uri'])
            Content.objects.all(), uri=kwargs['uri'])

    def get(self, request, *args, **kwargs):
        # if not request.user.is_authenticated:
        #     raise Http404()
        content_instance = self.get_instance(request, **kwargs)
        file_size = content_instance.lbrynet_data['total_bytes']
        real_file_size = content_instance.get_physical_file().stat().st_size
        if real_file_size != file_size:
            log.warning(
                'File mismatch: %s - %s (%s bytes difference)',
                file_size, real_file_size, file_size - real_file_size
            )
        file_handle = content_instance.get_physical_file().open(mode='rb')
        file_type = content_instance.get_mime_type()
        first_byte, last_byte = file_utils.parse_range_header(
            request.META.get('HTTP_RANGE', ''), file_size)
        log.info(
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

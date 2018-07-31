from django.conf import settings
from rest_framework.exceptions import APIException


class FileExtensionError(APIException):
    status_code = 400
    default_detail = 'Invalid file extension'


class TooLargeFile(APIException):
    status_code = 400
    default_detail = f'File cannot be larger than {settings.MAX_FILE_SIZE/1000000} MB'

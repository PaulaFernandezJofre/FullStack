"""
Custom Exception Handler
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'error': True,
            'status_code': response.status_code,
        }
        
        if isinstance(response.data, dict):
            custom_response['message'] = response.data.get('detail', str(response.data))
            custom_response['errors'] = response.data
        else:
            custom_response['message'] = str(response.data)
        
        response.data = custom_response
    
    return response

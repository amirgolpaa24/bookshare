from django.conf.urls import url
from django.urls import include, path

from .views import (api_register_borrow_request_view, api_get_borrow_list_view, 
                    api_get_lend_list_view, api_get_exchange_properties_view, 
                    api_add_borrow_response_view, )


app_name = 'sharing'

urlpatterns = [
    path('<book_slug>/borrow_request', api_register_borrow_request_view, name='send_borrow_request'),
    path('<exchange_slug>/borrow_response', api_add_borrow_response_view, name='send_borrow_response'),
    path('borrow_list', api_get_borrow_list_view, name='get_borrow_list'),
    path('lend_list', api_get_lend_list_view, name='get_lend_list'),
    path('exchange_properties/<exchange_slug>', api_get_exchange_properties_view, name='get_exchange_properties'),

]




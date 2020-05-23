from django.conf.urls import url
from django.urls import include, path

from .views import (api_add_book_view, api_edit_book_view, api_get_book_properties_view, 
                    api_delete_book_view, api_edit_book_image_view, api_get_book_image_view, )


app_name = 'book'

urlpatterns = [
    path('add_book', api_add_book_view, name='add_book'),
    path('<book_slug>/edit_book', api_edit_book_view, name='edit_book'),
    
    path('edit_image', api_edit_book_image_view, name='edit_book_image'),

    path('<book_slug>/book_image', api_get_book_image_view, name='get_book_image'),
    path('<book_slug>/delete_book', api_delete_book_view, name='delete_book'),
    path('<book_slug>/properties', api_get_book_properties_view, name='get_book_properties'),

    # path('debug', debug_view)

]


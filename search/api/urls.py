from django.conf.urls import url
from django.urls import include, path

from .views import (api_search_book_view, api_search_user_view, )


app_name = 'sharing'

urlpatterns = [
    path('search/book>', api_search_book_view, name='search_book'),
    path('search/user>', api_search_user_view, name='search_user'),
    
]




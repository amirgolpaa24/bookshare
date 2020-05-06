from django.conf.urls import url
from django.urls import include, path

from .views import (ChangePasswordView, ObtainAuthTokenView, activate,
                    api_account_properties_view, api_edit_account_view,
                    api_register_user_view, api_reset_password_view,
                    api_edit_image_view, api_get_profile_image_view,)
                    # delete_all_images, get_all_images_names, get_user_imiage_name, get_that_image)

app_name = 'account'

urlpatterns = [
    path('change_password', ChangePasswordView.as_view(), name='change_password'),
    path('edit', api_edit_account_view, name='edit_account'),
    path('edit_image', api_edit_image_view, name='edit_image'),
    path('login', ObtainAuthTokenView.as_view(), name='login'),
    path('<username>/profile_image', api_get_profile_image_view, name='get_profile_image'),
    path('register', api_register_user_view, name='register'),
    path('reset_password', api_reset_password_view, name='reset_password'),
    path('<username>/properties', api_account_properties_view, name='account_properties'),
    
    ##################################################################
    # path('getamirimages', get_all_images_names, name='x'),
    # path('getamirthatimage', get_that_image, name='x'),
    # path('deleteamirimages/<image_name>', delete_all_images, name='y'),
    # path('getamirimagename/<username>', get_user_imiage_name, name='z'),
    ##################################################################
    
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        activate, name='activate'),
    
]

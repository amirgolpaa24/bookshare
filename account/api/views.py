from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes)
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from account.tokens import account_activation_token

from .serializers import (ChangePasswordSerializer, EditedUserSerializer,
                          SelfUserSerializer, UserRegisterationSerializer,
                          UserSerializer)


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def api_register_user_view(request):
    
    if request.method == 'POST':        
        data = {}

        email = request.data.get('email', '0_no_email_provided_0').lower()
        username = request.data.get('username', '0_no_username_provided_0')
        first_name = request.data.get('first_name', '0_no_first_name_provided_0')
        last_name = request.data.get('last_name', '0_no_last_name_provided_0')
        password = request.data.get('password', '0_no_password_provided_0')
        password_confirmation = request.data.get('password_confirmation', '0_no_password_confirmation_provided_0')
        image = request.data.get('image', '0_no_image_provided_0')

        if email == '0_no_email_provided_0' or email == '':
            data['message'] = 'No email was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if username == '0_no_username_provided_0' or username == '':
            data['message'] = 'No username was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if first_name == '0_no_first_name_provided_0' or first_name == '':
            data['message'] = 'No first name was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if last_name == '0_no_last_name_provided_0' or last_name == '':
            data['message'] = 'No last name was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password == '0_no_password_provided_0' or password == '':
            data['message'] = 'No password was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password_confirmation == '0_no_password_confirmation_provided_0' or password_confirmation == '':
            data['message'] = 'No password confirmation was provided!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        
        if validate_email(email) is not None:
            data['message'] = 'Sorry, user with this email already exists!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if validate_username(username) is not None:
            data['message'] = 'Sorry, user with this username already exists!'
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password != password_confirmation:
            data['message'] = 'Passwords must match!'
            return Response(data, status.HTTP_400_BAD_REQUEST)

        # lowercase email:
        request_data = request.data.copy()
        request_data.pop('email', '0')
        request_data['email'] = email.lower()

        # serializing:
        serializer = UserRegisterationSerializer(data=request_data)

        if serializer.is_valid():
            new_user = serializer.save()

            # email verification:
            new_user.is_active = False
            new_user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate Your BookShare Account'
            activation_token = account_activation_token.make_token(new_user)
            mail_message = render_to_string('activate_email_email.html', {
                        'user': new_user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                        'token': activation_token,
                    })
           
            email_destination = email
            EmailMessage(mail_subject, mail_message, to=[email_destination]).send()
            return Response({'message': 'Please confirm your email address to complete the registration.'}, status=status.HTTP_200_OK)
        
        else:
            data = serializer.errors
            data['message'] = 'invalid fields'
            return Response(data, status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@permission_classes([])
@authentication_classes([])
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        data = {}
        data['message'] = 'You have successfully registered your account.'
        token = Token.objects.get(user=user).key
        data['token'] = token
        data['username'] = user.username
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['image'] = get_user_profile_image(user)

        return Response(data, status=status.HTTP_200_OK)

    else:
        return Response({'message': 'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)


def get_user_profile_image(user):
    image = user.image
    if image is not None:
        ####################
        image = 'no image'
        return image
    return 'no image'


def validate_email(email):
    user_with_this_email = None
    try:
        user_with_this_email = User.objects.get(email=email)
    except User.DoesNotExist:
        return None
    if user_with_this_email is not None:
        if is_user_expired(user_with_this_email):
            user_with_this_email.delete()
            return validate_email(email)
        else:
            return email
    return None


def validate_username(username):
    user_with_this_username = None
    try:
        user_with_this_username = User.objects.get(username=username)
    except User.DoesNotExist:
        return None
    if user_with_this_username is not None:
        if is_user_expired(user_with_this_username):
            user_with_this_username.delete()
            return validate_email(username)
        else:
            return username
    return None


def is_user_expired(user):
    if user.is_active:
        return False
    now_time = datetime.now()
    user_date_joined = user.date_joined.replace(tzinfo=None)
    if now_time - user_date_joined < timedelta(minutes=10):
        return False
    return True


class ObtainAuthTokenView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        data = {}
        user = authenticate(username=username, password=password)

        if user:
            try:
                token = Token.objects.get(user=user)
            except Token.DoesNotExist:
                token = Token.objects.create(user=user)
            data['message'] = 'You successfully logged in to your account.'
            data['token'] = token.key
            data['username'] = user.username
            data['email'] = user.email
            data['first_name'] = user.first_name
            data['last_name'] = user.last_name
            data['image'] = get_user_profile_image(user)
            return Response(data, status=status.HTTP_200_OK)
        else:
            data['message'] = 'Wrong username or password'
            return Response(data, status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@permission_classes((IsAuthenticated,))
def api_account_properties_view(request, username):

    if request.method == 'GET':
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'message': 'There is no such username!'}, status=status.HTTP_404_NOT_FOUND)

        requester = request.user
        is_outsider = (user != requester)

        serializer = UserSerializer(user)
        if not is_outsider:
            serializer = SelfUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', ])
@permission_classes((IsAuthenticated,))
def api_edit_account_view(request):

    if request.method == 'PUT':
        print('\n-------------------\n')
        user = request.user

        editable_fields = ['first_name', 'last_name', 'username']
        if not any([field in request.data for field in editable_fields]):
            return Response(data={'message': 'No changes have been made.'}, status=status.HTTP_400_BAD_REQUEST)
        
        request_data = {}
        for field in editable_fields:
            if field in request.data:
                request_data[field] = request.data[field]

        serializer = EditedUserSerializer(user, data=request_data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(data={'message': 'You have successfully updated your account.'}, status=status.HTTP_200_OK)
        else:
            data = serializer.errors
            data['message'] = 'invalid fields'
            return Response(data, status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"message": "The old password is wrong!"}, status=status.HTTP_400_BAD_REQUEST)

            # confirm the new passwords match
            new_password = serializer.data.get("new_password")
            confirm_new_password = serializer.data.get("new_password_confirmation")
            if new_password != confirm_new_password:
                return Response({"message": "New passwords must match!"}, status=status.HTTP_400_BAD_REQUEST)

            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"message": "You have successfully changed your password."}, status=status.HTTP_200_OK)
        else:
            serializer_errors = serializer.errors
            error_message = ''
            for field in ['old_password', 'new_password', 'new_password_confirmation']:
                if field in serializer_errors:
                    error_message += 'The ' + field.replace('_', ' ')  + ' is required!\n'
            if error_message.endswith('\n'):
                error_message = error_message[:len(error_message) - 1]
            data = {'message': error_message}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
                    
        
@api_view(['POST', ])
@permission_classes((IsAuthenticated,))
def api_reset_password_view(request):
    
    if request.method == 'POST':
        
        email = request.data.get('email', '0_no_email_provided_0').lower()
        data = {}
        
        if email == '0_no_email_provided_0' or email == '':
            data['message'] = 'No email was provided!'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if (not user.is_active) or user.email != email:
            data['message'] = 'This email is not verified in your account!'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()

        # sending email with new password:
        mail_subject = 'Retrieve your account'
        mail_message = render_to_string('reset_password_email.html', {
                    'user': user,
                    'new_password': new_password,
                })
        
        email_destination = email
        EmailMessage(mail_subject, mail_message, to=[email_destination]).send()
        return Response({'message': 'Your password has successfully changed;\nWe sent your new password to your email account.'}, status=status.HTTP_200_OK)

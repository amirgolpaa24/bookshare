from datetime import datetime, timedelta

from bookshare.settings import MSG_LANGUAGE

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


# messages:
MSG_NO_EMAIL =                  {'Persian': 'رایانامه ارائه نشده است', 'English': 'No email was provided!'}[MSG_LANGUAGE]
MSG_NO_USERNAME =               {'Persian': 'نام کاربری ارائه نشده است', 'English': 'No username was provided!'}[MSG_LANGUAGE]
MSG_NO_FIRSTNAME =              {'Persian': 'نام کوچک ارائه نشده است', 'English': 'No first name was provided!'}[MSG_LANGUAGE]
MSG_NO_LASTNAME =               {'Persian': 'نام خانوادگی ارائه نشده است', 'English': 'No last name was provided!'}[MSG_LANGUAGE]
MSG_NO_PASSWORD =               {'Persian': 'رمز عبور ارائه نشده است', 'English': 'No password was provided!'}[MSG_LANGUAGE]
MSG_NO_PASSWORDCONFIRMATION =   {'Persian': 'تکرار رمز عبور ارائه نشده است', 'English': 'No password confirmation was provided!'}[MSG_LANGUAGE]
MSG_DUPLICATE_EMAIL =           {'Persian': 'متاسفانه کاربری با این رایانامه وجود دارد', 'English': 'Sorry, user with this email already exists!'}[MSG_LANGUAGE]
MSG_DUPLICATE_USERNAME =        {'Persian': 'متاسفانه کاربری با این نام کاربری وجود دارد', 'English': 'Sorry, user with this username already exists!'}[MSG_LANGUAGE]
MSG_NONMATH_PASSWORDS =         {'Persian': 'رمز عبور و تکرار آن یکسان نیستند', 'English': 'Passwords must match!'}[MSG_LANGUAGE]
MSG_INVALID_FIELDS =            {'Persian': 'ورودی (های) نامعتبر', 'English': 'invalid fields'}[MSG_LANGUAGE]
MSG_INVALID_LINK =              {'Persian': 'لینک فعال سازی نامعتبر است', 'English': 'Activation link is invalid!'}[MSG_LANGUAGE]
MSG_WRONG_USERNAMEPASSWORD =    {'Persian': 'نام کاربری یا رمز عبور اشتباه است', 'English': 'Wrong username or password!'}[MSG_LANGUAGE]
MSG_WRONG_OLDPASSWORD =         {'Persian': 'رمز عبور قدیمی اشتباه است', 'English': "The old password is wrong!"}[MSG_LANGUAGE]
MSG_NONEXISTANT_USERNAME =      {'Persian': 'چنین کاربری وجود ندارد', 'English': 'There is no such username!'}[MSG_LANGUAGE]
MSG_NONVERIFIED_EMAIL =         {'Persian': 'این رایانامه فاقد اعتبار کاربری است', 'English': 'This email is not verified yet!'}[MSG_LANGUAGE]
MSG_CANNOT_RETRIEVE =           {'Persian': 'متاسفانه بازیابی رمز عبور فعلا برای شما ممکن نمی باشد', 'English': 'Sorry, you cannot retrieve your account for now.'}[MSG_LANGUAGE]
MSG_NO_CHANGES =                {'Persian': 'هیچ تغییری اعمال نگردید', 'English': 'No changes have been made.'}[MSG_LANGUAGE]

MSG_REGISTER_SUCCESS =          {'Persian': 'شما با موفقیت ثبت نام کردید', 'English': 'You have successfully registered your account.'}[MSG_LANGUAGE]
MSG_LOGIN_SUCCESS =             {'Persian': 'شما با موفقیت وارد حساب کاربری خود شدید', 'English': 'You successfully logged in to your account.'}[MSG_LANGUAGE]
MSG_EDIT_SUCCESS =              {'Persian': 'شما با موفقیت اطلاعات حساب خود را تغییر دادید', 'English': 'You have successfully updated your account.'}[MSG_LANGUAGE]
MSG_CHANGEPASSWORD_SUCCESS =    {'Persian': 'شما با موفقیت رمز عبور خود را تغییر دادید', 'English': 'You have successfully changed your password.'}[MSG_LANGUAGE]
MSG_RESETPASSWORD_SUCCESS =     {'Persian': 'رمز عبور شما با موفقیت تغییر کرد.\n رمز عبور جدید به رایانامه شما فرستاده شده است.', 'English': 'Your password has successfully changed;\nWe sent your new password to your email account.'}[MSG_LANGUAGE]


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
            data['message'] = MSG_NO_EMAIL
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if username == '0_no_username_provided_0' or username == '':
            data['message'] = MSG_NO_USERNAME
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if first_name == '0_no_first_name_provided_0' or first_name == '':
            data['message'] = MSG_NO_FIRSTNAME
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if last_name == '0_no_last_name_provided_0' or last_name == '':
            data['message'] = MSG_NO_LASTNAME
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password == '0_no_password_provided_0' or password == '':
            data['message'] = MSG_NO_PASSWORD
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password_confirmation == '0_no_password_confirmation_provided_0' or password_confirmation == '':
            data['message'] = MSG_NO_PASSWORDCONFIRMATION
            return Response(data, status.HTTP_400_BAD_REQUEST)
        
        if validate_email(email) is not None:
            data['message'] = MSG_DUPLICATE_EMAIL
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if validate_username(username) is not None:
            data['message'] = MSG_DUPLICATE_USERNAME
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password != password_confirmation:
            data['message'] = MSG_NONMATH_PASSWORDS
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
            data['message'] = MSG_INVALID_FIELDS
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
        data['message'] = MSG_REGISTER_SUCCESS
        token = Token.objects.get(user=user).key
        data['token'] = token
        data['username'] = user.username
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['image'] = get_user_profile_image(user)

        return Response(data, status=status.HTTP_200_OK)

    else:
        user.is_active = False
        return Response({'message': MSG_INVALID_LINK}, status=status.HTTP_400_BAD_REQUEST)


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
        username = request.data.get('username', '0_no_username_provided_0')
        password = request.data.get('password', '0_no_password_provided_0')

        data = {}
        if username == '0_no_username_provided_0' or username == '':
            data['message'] = MSG_NO_USERNAME
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if password == '0_no_password_provided_0' or password == '':
            data['message'] = MSG_NO_PASSWORD
            return Response(data, status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user:
            try:
                token = Token.objects.get(user=user)
            except Token.DoesNotExist:
                token = Token.objects.create(user=user)
            data['message'] = MSG_LOGIN_SUCCESS
            data['token'] = token.key
            data['username'] = user.username
            data['email'] = user.email
            data['first_name'] = user.first_name
            data['last_name'] = user.last_name
            data['image'] = get_user_profile_image(user)
            return Response(data, status=status.HTTP_200_OK)
        else:
            data['message'] = MSG_WRONG_USERNAMEPASSWORD
            return Response(data, status.HTTP_400_BAD_REQUEST)


@api_view(['GET', ])
@permission_classes((IsAuthenticated,))
def api_account_properties_view(request, username):

    if request.method == 'GET':
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'message': MSG_NONEXISTANT_USERNAME}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({'message': MSG_NONEXISTANT_USERNAME}, status=status.HTTP_404_NOT_FOUND)

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
        user = request.user

        editable_fields = ['first_name', 'last_name', 'username']
        if not any([field in request.data for field in editable_fields]):
            return Response(data={'message': MSG_NO_CHANGES}, status=status.HTTP_400_BAD_REQUEST)
        
        request_data = {}
        for field in editable_fields:
            if field in request.data:
                request_data[field] = request.data[field]

        serializer = EditedUserSerializer(user, data=request_data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(data={'message': MSG_EDIT_SUCCESS}, status=status.HTTP_200_OK)
        else:
            data = serializer.errors
            data['message'] = MSG_INVALID_FIELDS
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
                return Response({"message": MSG_WRONG_OLDPASSWORD}, status=status.HTTP_400_BAD_REQUEST)

            # confirm the new passwords match
            new_password = serializer.data.get("new_password")
            confirm_new_password = serializer.data.get("new_password_confirmation")
            if new_password != confirm_new_password:
                return Response({"message": MSG_NONMATH_PASSWORDS}, status=status.HTTP_400_BAD_REQUEST)

            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"message": MSG_CHANGEPASSWORD_SUCCESS}, status=status.HTTP_200_OK)
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
@permission_classes([])
@authentication_classes([])
def api_reset_password_view(request):
    
    if request.method == 'POST':
        
        email = request.data.get('email', '0_no_email_provided_0').lower()
        data = {}
        
        if email == '0_no_email_provided_0' or email == '':
            data['message'] = MSG_NO_EMAIL
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            data['message'] = MSG_NONVERIFIED_EMAIL
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        if (not user.is_active):
            data['message'] = MSG_NONVERIFIED_EMAIL
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        if user.last_retrieval is not None and (datetime.now() - user.last_retrieval) < timedelta(hour=1):
            data['message'] = MSG_CANNOT_RETRIEVE
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # if ok:
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()

        # setting the limitation:
        user.last_retrieval = datetime.now()
        user.save()

        # sending email with new password:
        mail_subject = 'Retrieve your account'
        mail_message = render_to_string('reset_password_email.html', {
                    'user': user,
                    'new_password': new_password,
                })
        
        email_destination = email
        EmailMessage(mail_subject, mail_message, to=[email_destination]).send()
        
        return Response({'message': MSG_RESETPASSWORD_SUCCESS}, status=status.HTTP_200_OK)

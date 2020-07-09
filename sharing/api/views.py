import json
import os

from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes)
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from book.models import Book
from bookshare.settings import DEFAULT_BOOK_IMAGE, MEDIA_ROOT, MSG_LANGUAGE
from sharing.models import BookExchange

from .serializers import (BookExchangeBorrowRequestSerializer,
                          BookExchangeRegistrationSerializer,
                          ExchangePropertiesSerializer,
                          UserBorrowListSerializer, UserLendListSerializer)

# messages:
MSG_NO_RESPONSE_RESULT =        {'Persian': 'نتیجه پاسخ ارائه نشده است', 'English': 'No response result was provided!'}[MSG_LANGUAGE]

MSG_IMPOSSIBLE_BORROW =         {'Persian': 'قرض گرفتن این کتاب ممکن نمی باشد', 'English': 'impossible borrowing!'}[MSG_LANGUAGE]
MSG_BOOK_UNAVAILABLE =          {'Persian': 'این کتاب در حال حاضر در دسترس نمی باشد', 'English': 'This book is unavailable!'}[MSG_LANGUAGE]

MSG_INVALID_FIELDS =            {'Persian': 'ورودی (های) نامعتبر', 'English': 'invalid fields!'}[MSG_LANGUAGE]
MSG_INVALID_STATE =             {'Persian': 'کتاب در وضعیت نامعتبر', 'English': 'invalid state!'}[MSG_LANGUAGE]

MSG_NONEXISTANT_BOOKEXCHANGE =  {'Persian': 'چنین مبادله کتابی وجود ندارد', 'English': 'There is no such book exchange!'}[MSG_LANGUAGE]
MSG_UNEXPECTED_STATE =          {'Persian': 'حالت اشتراک کتاب در محدوده مورد نظر نیست', 'English': 'The exchange is not in the expected range!'}[MSG_LANGUAGE]

MSG_BORROW_REQUEST_SUCCESS =    {'Persian': 'درخواست قرض گرفتن کتاب با موفقیت ثبت شد', 'English': 'Your book borrow request was successfully registered.'}[MSG_LANGUAGE]
MSG_BORROW_RESPONSE_SUCCESS =    {'Persian': 'پاسخ شما به این درخواست با موفقیت ثبت شد', 'English': 'Your reponse to this request was successfully registered.'}[MSG_LANGUAGE]

MSG_REJECT_RESPONSE_SUCCESS =   {'Persian': 'پاسخ رد با موفقیت ارسال شد', 'English': 'Your book reject response was successfully sent.'}[MSG_LANGUAGE]
MSG_ACCEPT_RESPONSE_SUCCESS =   {'Persian': 'پاسخ قبول با موفقیت ارسال شد', 'English': 'Your book accept response was successfully sent.'}[MSG_LANGUAGE]
MSG_BOOK_DELIVERY_SUCCESS =     {'Persian': 'کتاب با موفقیت تحویل داده شد', 'English': 'Your book was delivered successfully sent.'}[MSG_LANGUAGE]
MSG_BOOK_RETURN_SUCCESS =       {'Persian': 'کتاب با موفقیت بازگردانده شد', 'English': 'Your book was returned successfully.'}[MSG_LANGUAGE]
MSG_BORROWER_RATING_SUCCESS =   {'Persian': 'ارزیابی شما از قرض گیرنده با موفقیت ثبت شد', 'English': 'Your rating for borrower was successfully sent.'}[MSG_LANGUAGE]


########################################################################################################################################


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_register_borrow_request_view(request, book_slug):

    if request.method == 'POST': 
        response_data = {}

        request_message = request.data.get('request_message', '')
        request_phone_number = request.data.get('request_phone_number', '')

        book = Book.objects.get(slug=book_slug)
        borrower = request.user
        lender = book.owner

        if lender == borrower:
            response_data['message'] = MSG_IMPOSSIBLE_BORROW
            return Response(response_data, status.HTTP_400_BAD_REQUEST)
        # if this book is in an active exchange:
        if BookExchange.objects.filter(book=book, state__in=[0, 2, 3]).exists():
            response_data['message'] = MSG_BOOK_UNAVAILABLE
            return Response(response_data, status.HTTP_400_BAD_REQUEST)

        serializer_data = {
            "borrower": borrower.pk,
            "book": book.pk,
        }
        book_exchange_serializer = BookExchangeRegistrationSerializer(data=serializer_data)


        if book_exchange_serializer.is_valid():
            new_book_exchange = book_exchange_serializer.save()
            
            # requesting:
            request_result = new_book_exchange.request(request_message=request_message, phone_number=request_phone_number)
            if request_result != True:
                new_book_exchange.delete()
                response_data = request_result
                response_data['message'] = MSG_INVALID_FIELDS
                return Response(response_data, status.HTTP_400_BAD_REQUEST)

            response_data['message'] = MSG_BORROW_REQUEST_SUCCESS
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = book_exchange_serializer.errors
            response_data['message'] = MSG_INVALID_FIELDS
            return Response(response_data, status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_add_borrow_response_view(request, exchange_slug):

    if request.method == 'PUT': 
        response_data = {}

        user = request.user

        try:
            book_exchange = BookExchange.objects.get(slug=exchange_slug)
            if book_exchange.lender != user:
                raise BookExchange.DoesNotExist
        except BookExchange.DoesNotExist:
            response_data['message'] = MSG_NONEXISTANT_BOOKEXCHANGE
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)

        response_result = request.data.get('response_result', '')
        if response_result not in ['accept', 'reject']:
            response_data['message'] = MSG_NO_RESPONSE_RESULT
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)

        # if rejected:
        if response_result == 'reject':
            reject_result = book_exchange.reject()
            if reject_result:
                response_data['message'] = MSG_REJECT_RESPONSE_SUCCESS
                return Response(data=response_data, status=status.HTTP_200_OK)
            else:
                response_data['message'] = MSG_INVALID_FIELDS
                return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)

        # if accepted:
        response_message = request.data.get('response_message', '')
        response_meeting_address = request.data.get('response_meeting_address', '')
        response_meeting_year = request.data.get('response_meeting_year', '')
        response_meeting_month = request.data.get('response_meeting_month', '')
        response_meeting_day = request.data.get('response_meeting_day', '')
        response_meeting_hour = request.data.get('response_meeting_hour', '')
        response_meeting_minute = request.data.get('response_meeting_minute', '')

        accept_result = book_exchange.accept(
            response_message = response_message,
            meeting_address = response_meeting_address,
            meeting_year = response_meeting_year,
            meeting_month = response_meeting_month,
            meeting_day = response_meeting_day,
            meeting_hour = response_meeting_hour,
            meeting_minute = response_meeting_minute,
        )
        
        if accept_result != True:
            if isinstance(accept_result, bool):
                response_data['message'] = MSG_INVALID_STATE
            else:
                response_data = accept_result
                response_data['message'] = MSG_INVALID_FIELDS
            return Response(response_data, status.HTTP_400_BAD_REQUEST)

        response_data['message'] = MSG_BORROW_RESPONSE_SUCCESS
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_get_borrow_list_view(request):
    """ this api returns a list of all the books one has received (borrowed)
        or all the requests (whether rejected or accepted) he/she has sent. """

    if request.method == 'GET': 
        response_data = {}

        user = request.user
        borrow_list_serializer = UserBorrowListSerializer(user)

        return Response(data=borrow_list_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_get_lend_list_view(request):
    """ this api returns a list of all the books one has sent (lent)
        or all the requests (only if accepted) he/she has received. """

    if request.method == 'GET': 
        response_data = {}

        user = request.user
        lend_list_serializer = UserLendListSerializer(user)

        return Response(data=lend_list_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_get_exchange_properties_view(request, exchange_slug):
    """ this api returns a book_exchange properties in details. """

    if request.method == 'GET': 
        response_data = {}

        user = request.user
        try:
            book_exchange = BookExchange.objects.get(slug=exchange_slug)
        except BookExchange.DoesNotExist:
            response_data['message'] = MSG_NONEXISTANT_BOOKEXCHANGE
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)

        exchange_serializer = ExchangePropertiesSerializer(book_exchange)

        return Response(data=exchange_serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_deliver_book_to_borrower_view(request, exchange_slug):

    if request.method == 'PUT': 
        response_data = {}

        user = request.user

        try:
            book_exchange = BookExchange.objects.get(slug=exchange_slug)
            if book_exchange.lender != user:
                raise BookExchange.DoesNotExist
        except BookExchange.DoesNotExist:
            response_data['message'] = MSG_NONEXISTANT_BOOKEXCHANGE
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)


        return_meeting_address = request.data.get('return_meeting_address', '')
        return_meeting_year = request.data.get('return_meeting_year', '')
        return_meeting_month = request.data.get('return_meeting_month', '')
        return_meeting_day = request.data.get('return_meeting_day', '')
        return_meeting_hour = request.data.get('return_meeting_hour', '')
        return_meeting_minute = request.data.get('return_meeting_minute', '')

        delivery_result = book_exchange.deliver(
            meeting_address = return_meeting_address,
            meeting_year = return_meeting_year,
            meeting_month = return_meeting_month,
            meeting_day = return_meeting_day,
            meeting_hour = return_meeting_hour,
            meeting_minute = return_meeting_minute,
        )
        
        if delivery_result != True:
            if isinstance(delivery_result, bool):
                response_data['message'] = MSG_INVALID_STATE
            else:
                mail_subject = 'Delivery Result'
                mail_message = str(delivery_result)
                email_destination = "amirgolpaa24@gmail.com"
                EmailMessage(mail_subject, mail_message, to=[email_destination]).send()

                response_data = delivery_result
                response_data['message'] = MSG_INVALID_FIELDS
            return Response(response_data, status.HTTP_400_BAD_REQUEST)

        response_data['message'] = MSG_BOOK_DELIVERY_SUCCESS
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_return_book_view(request, exchange_slug):

    if request.method == 'PUT': 
        response_data = {}

        user = request.user

        try:
            book_exchange = BookExchange.objects.get(slug=exchange_slug)
            if book_exchange.borrower != user:
                raise BookExchange.DoesNotExist
        except BookExchange.DoesNotExist:
            response_data['message'] = MSG_NONEXISTANT_BOOKEXCHANGE
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)


        lender_rating = request.data.get('lender_rating', '')
        book_rating = request.data.get('book_rating', '')
        book_comment = request.data.get('book_comment', '')

        end_result = book_exchange.end(
            lender_rating = lender_rating,
            book_rating = book_rating,
            book_comment = book_comment
        )
        
        if end_result != True:
            if isinstance(end_result, bool):
                response_data['message'] = MSG_INVALID_STATE
            else:
                response_data = end_result
                response_data['message'] = MSG_INVALID_FIELDS
            return Response(response_data, status.HTTP_400_BAD_REQUEST)

        response_data['message'] = MSG_BOOK_RETURN_SUCCESS
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_rate_borrower_view(request, exchange_slug):

    if request.method == 'PUT': 
        response_data = {}

        user = request.user

        try:
            book_exchange = BookExchange.objects.get(slug=exchange_slug)
            if book_exchange.lender != user:
                raise BookExchange.DoesNotExist
        except BookExchange.DoesNotExist:
            response_data['message'] = MSG_NONEXISTANT_BOOKEXCHANGE
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)


        borrower_rating = request.data.get('borrower_rating', '')
        end_result = book_exchange.rate_borrower(borrower_rating = borrower_rating)
        
        if end_result != True:
            if isinstance(end_result, bool):
                response_data['message'] = MSG_INVALID_STATE
            else:
                response_data = end_result
                response_data['message'] = MSG_INVALID_FIELDS
            return Response(response_data, status.HTTP_400_BAD_REQUEST)

        response_data['message'] = MSG_BORROWER_RATING_SUCCESS
        return Response(response_data, status=status.HTTP_200_OK)

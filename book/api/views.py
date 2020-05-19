from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.http import HttpResponse
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
from book.models import Author, Book
from bookshare.settings import (MSG_LANGUAGE, MEDIA_ROOT, DEFAULT_BOOK_IMAGE)

from .serializers import (  AuthorSerializer, AddBookSerializer, BookSerializer, 
                            SelfBookSerializer, EditBookSerializer, EditBookImageSerializer, )
import os


# messages:
MSG_NO_TITLE =                  {'Persian': 'عنوان ارائه نشده است', 'English': 'No title was provided!'}[MSG_LANGUAGE]
MSG_NO_DESCRIPTION =            {'Persian': 'توضیحات ارائه نشده است', 'English': 'No description was provided!'}[MSG_LANGUAGE]
MSG_NO_PAGENUM =                {'Persian': 'تعداد صفحات ارائه نشده است', 'English': 'No page number was provided!'}[MSG_LANGUAGE]
MSG_NO_CATEGORY =               {'Persian': 'دسته ارائه نشده است', 'English': 'No category was provided!'}[MSG_LANGUAGE]
MSG_NO_AUTHORS =                {'Persian': 'نویسنده ارائه نشده است', 'English': 'No author was provided!'}[MSG_LANGUAGE]
MSG_NO_IMAGE =                  {'Persian': 'تصویر ارائه نشده است', 'English': 'No image was provided!'}[MSG_LANGUAGE]
MSG_AUTHORS_NOTLIST =           {'Persian': 'لیستی از نویسنده ارائه نشده است', 'English': "No authors' list was provided!"}[MSG_LANGUAGE]
MSG_INVALID_AUTHORS =           {'Persian': 'نام نویسنده نامعتبر', 'English': 'invalid author name!'}[MSG_LANGUAGE]
MSG_INVALID_FIELDS =            {'Persian': 'ورودی (های) نامعتبر', 'English': 'invalid fields!'}[MSG_LANGUAGE]
MSG_NONEXISTANT_USERNAME =      {'Persian': 'چنین کاربری وجود ندارد', 'English': 'There is no such username!'}[MSG_LANGUAGE]
MSG_WRONG_USERNAME =            {'Persian': 'نام کاربری اشتباه است', 'English': 'The username is wrong!'}[MSG_LANGUAGE]
MSG_NONEXISTANT_BOOK =          {'Persian': 'چنین کتابی وجود ندارد', 'English': 'There is no such book!'}[MSG_LANGUAGE]
MSG_NOTYOURS_BOOK =             {'Persian': 'این کتاب متعلق به شما نیست', 'English': 'This book is not yours!'}[MSG_LANGUAGE]

MSG_EDIT_IMAGE_SUCCESS =        {'Persian': 'شما با موفقیت تصویر کتاب را تغییر دادید', 'English': 'You have successfully updated your book image.'}[MSG_LANGUAGE]
MSG_DELETE_BOOK_SUCCESS =       {'Persian': 'کتاب شما با موفقیت حذف شد', 'English': 'Your book was successfully deleted.'}[MSG_LANGUAGE]
MSG_ADD_BOOK_SUCCESS =          {'Persian': 'کتاب شما با موفقیت ثبت شد', 'English': 'Your book was successfully added.'}[MSG_LANGUAGE]
MSG_EDIT_BOOK_SUCCESS =         {'Persian': 'اطلاعات کتاب شما با موفقیت ویرایش شد', 'English': 'Your book was successfully edited.'}[MSG_LANGUAGE]

########################################################################################################################################


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_add_book_view(request):
    
    if request.method == 'POST':        
        data = {}

        title =         request.data.get('title', None)
        description =   request.data.get('description', None)
        page_num =      request.data.get('page_num', None)
        category_1 =    request.data.get('category_1', None)
        authors =       request.data.get('authors', None)

        edition =       request.data.get('edition', None)
        publisher =     request.data.get('publisher', None)
        pub_year =      request.data.get('pub_year', None)
        category_2 =    request.data.get('category_2', None)
        category_3 =    request.data.get('category_3', None)
        image =         request.data.get('image', None)
        
        if title is None or title == '':
            data['message'] = MSG_NO_TITLE
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if description is None or description == '':
            data['message'] = MSG_NO_DESCRIPTION
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if page_num is None or page_num == '':
            data['message'] = MSG_NO_PAGENUM
            return Response(data, status.HTTP_400_BAD_REQUEST)
        if category_1 is None or category_1 == '':
            data['message'] = MSG_NO_CATEGORY
            return Response(data, status.HTTP_400_BAD_REQUEST)
        
        author_names = []
        if authors is None or type(authors) != list:
            data['message'] = MSG_AUTHORS_NOTLIST
            return Response(data, status.HTTP_400_BAD_REQUEST)
        elif authors == []:
            data['message'] = MSG_NO_AUTHORS
            return Response(data, status.HTTP_400_BAD_REQUEST)
        else: 
            for author_name in authors:
                if author_name is None or author_name == '':
                    data['message'] = MSG_INVALID_AUTHORS
                    return Response(data, status.HTTP_400_BAD_REQUEST)
                author_names.append(author_name)
                
        book_request_data = request.data.copy()
        book_request_data.pop('authors')

        owner = request.user.pk
        book_request_data['owner'] = owner

        # serializing books:
        book_serializer = AddBookSerializer(data=book_request_data, partial=True)

        if book_serializer.is_valid():
            new_book = book_serializer.save()

            # serializing authors:
            author_serializers = []
            for author_name in author_names:
                author_i_serializer = AuthorSerializer(data={'name': author_name, 'book': new_book.pk})
                author_serializers.append(author_i_serializer)

            if any([not author_i_serializer.is_valid() for author_i_serializer in author_serializers]):
                data = author_i_serializer.errors
                data['message'] = MSG_INVALID_FIELDS
                new_book.delete()
                return Response(data, status.HTTP_400_BAD_REQUEST)

            for author_i_serializer in author_serializers:
                author_i_serializer.save()

            return Response({'message': MSG_ADD_BOOK_SUCCESS}, status=status.HTTP_200_OK)
        else:
            data = book_serializer.errors
            data['message'] = MSG_INVALID_FIELDS
            return Response(data, status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_edit_book_view(request, book_slug):

    if request.method == 'PUT':        
        data = {}

        requester = request.user

        # checking if the book exists and belongs to the requester:
        try:
            book = Book.objects.get(slug=book_slug)
            if book.owner != requester:
                data['message'] = MSG_NOTYOURS_BOOK
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            data['message'] = MSG_NONEXISTANT_BOOK
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # serializing:
        serializer = EditBookSerializer(book, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            data['message'] = MSG_EDIT_BOOK_SUCCESS
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            data = serializer.errors
            data['message'] = MSG_INVALID_FIELDS
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_delete_book_view(request, book_slug):

    if request.method == 'DELETE':        
        data = {}
        
        requester = request.user
        
        # checking if the book exists and belongs to the requester:
        try:
            book = Book.objects.get(slug=book_slug)
            if book.owner != requester:
                data['message'] = MSG_NOTYOURS_BOOK
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            data['message'] = MSG_NONEXISTANT_BOOK
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # deleting the book:
        book.delete()

        data['message'] = MSG_DELETE_BOOK_SUCCESS
        return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_get_book_properties_view(request, book_slug):

    if request.method == 'GET':        
        data = {}
        
        requester = request.user

        # checking if the book exists:
        try:
            book = Book.objects.get(slug=book_slug)
        except Book.DoesNotExist:
            data['message'] = MSG_NONEXISTANT_BOOK
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # serializing:
        serializer = BookSerializer(book)
        if book.owner == requester:
            serializer = SelfBookSerializer(book)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


################### image related api's ######################


def remove_old_book_image(book):
    path = os.listdir(os.path.join(MEDIA_ROOT, 'book_images'))
    for book_image_name in path:
        if book_image_name.startswith(str(book.pk) + '-'):
            os.remove(os.path.join(MEDIA_ROOT, 'book_images', book_image_name))
            break
    return


@api_view(['PUT', ])
@permission_classes(())
@authentication_classes((TokenAuthentication,))
def api_edit_book_image_view(request, book_slug):
    
    if request.method == 'PUT':
    
        data = {}

        requester = request.user

        # checking if the book exists and belongs to the requester:
        try:
            book = Book.objects.get(slug=book_slug)
            if book.owner != requester:
                data['message'] = MSG_NOTYOURS_BOOK
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            data['message'] = MSG_NONEXISTANT_BOOK
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # extracting image from request json object:
        image = request.data.get('image', None)
        if not(image):
            data['message'] = MSG_NO_IMAGE
            return Response(data, status.HTTP_400_BAD_REQUEST)
        
        # serializing:
        serializer = EditBookImageSerializer(book, data={'image': image})
        if serializer.is_valid():
            remove_old_book_image(book)
            serializer.save()
            data['message'] = MSG_EDIT_IMAGE_SUCCESS
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            data = serializer.errors
            data['message'] = MSG_INVALID_FIELDS
            return Response(data, status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET', ])
@permission_classes(())
@authentication_classes((TokenAuthentication,))
def api_get_book_image_view(request, book_slug):
    
    if request.method == 'GET':

        data = {}   

        # checking if the book exists:
        try:
            book = Book.objects.get(slug=book_slug)
        except Book.DoesNotExist:
            data['message'] = MSG_NONEXISTANT_BOOK
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        DEFAULT_BOOK_IMAGE_PATH = os.path.join(MEDIA_ROOT, DEFAULT_BOOK_IMAGE)
        image_path = DEFAULT_BOOK_IMAGE_PATH
        try:
            if book.image is not None:
                image_path = book.image.path
        except ValueError:
            pass
    
        try:
            with open(image_path, "rb") as image_file:
                return HttpResponse(image_file.read(), content_type="image/jpeg")
        except IOError as e:
            with open(DEFAULT_BOOK_IMAGE_PATH, "rb") as image_file:
                return HttpResponse(image_file.read(), content_type="image/jpeg")










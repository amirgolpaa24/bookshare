from math import log2

from django.contrib.auth import authenticate
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.db.models import CharField, F, Value
from django.db.models.functions import Concat
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from book.models import Author, Book
from bookshare.settings import DEFAULT_BOOK_IMAGE, MEDIA_ROOT, MSG_LANGUAGE

from .serializers import BookResultSerializer, UserResultSerializer


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([])
def api_search_book_view(request):

    if request.method == 'PUT':        
        response_data = {}

        query = request.data.get("query", None)
        if query is None:
            response_data["message"] = "Erro - No Query!"
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)


        # searching query in book "title":
        title_res = Book.objects.annotate(
            rank=SearchRank(SearchVector('title'), SearchQuery(query)),
        ).filter(rank__gt=0.0)
        title_res = sorted(title_res, key=lambda b: b.rank * (1 + log2(1 + b.rating)), reverse=True)
        title_scores = {b.pk: b.rank * (1 + log2(1 + b.rating)) for b in title_res}
        if title_res != []:
            max_title_score = title_scores[title_res[0].pk]
            title_scores = {b: title_scores[b] / max_title_score for b in title_scores}

        # searching query in book "description":
        description_res = Book.objects.annotate(
            rank=SearchRank(SearchVector('description'), SearchQuery(query)),
        ).filter(rank__gt=0.0)
        description_res = sorted(description_res, key=lambda b: b.rank * (1 + log2(1 + b.rating)), reverse=True)
        description_scores = {b.pk: b.rank * (1 + log2(1 + b.rating)) for b in description_res}
        if description_res != []:
            max_description_score = description_scores[description_res[0].pk]
            description_scores = {b: description_scores[b] / max_description_score for b in description_scores}

        # searching query in book "author":
        author_res = Book.objects.annotate(
            rank=SearchRank(SearchVector('authors_str'), SearchQuery(query)),
        ).filter(rank__gt=0.0)
        author_res = sorted(author_res, key=lambda b: b.rank * (1 + log2(1 + b.rating)), reverse=True)
        author_scores = {b.pk: b.rank * (1 + log2(1 + b.rating)) for b in author_res}
        if author_res != []:
            max_author_score = author_scores[author_res[0].pk]
            author_scores = {b: author_scores[b] / max_author_score for b in author_scores}

        # searching query in book "publisher":
        publisher_res = Book.objects.annotate(
            rank=SearchRank(SearchVector('publisher'), SearchQuery(query)),
        ).filter(rank__gt=0.0)
        publisher_res = sorted(publisher_res, key=lambda b: b.rank * (1 + log2(1 + b.rating)), reverse=True)
        publisher_scores = {b.pk: b.rank * (1 + log2(1 + b.rating)) for b in publisher_res}
        if publisher_res != []:
            max_publisher_score = publisher_scores[publisher_res[0].pk]
            publisher_scores = {b:publisher_scores[b] / max_publisher_score for b in publisher_scores}


        # combining:
        weights = {"title": 0.5, "description": 0.25, "author": 0.15, "publisher": 0.1}

        final_scores = {x: 0.0 for x in set(title_scores.keys()).union(set(description_scores.keys()), set(author_scores.keys()), set(publisher_scores.keys()))}
        for book_pk in final_scores:
            final_score =   weights["title"] * title_scores.get(book_pk, 0.0) + \
                            weights["description"] * description_scores.get(book_pk, 0.0) + \
                            weights["author"] * author_scores.get(book_pk, 0.0) + \
                            weights["publisher"] * publisher_scores.get(book_pk, 0.0)
            final_scores[book_pk] = final_score
        
        final_scores = [Book.objects.get(pk=b_pk) for b_pk in sorted(list(final_scores.keys()), key=lambda bpk: final_scores[bpk], reverse=True)]
        serializer = BookResultSerializer(final_scores, many=True)

        return Response(data={"result": serializer.data}, status=status.HTTP_200_OK)


@api_view(['PUT', ])
@permission_classes([])
@authentication_classes([TokenAuthentication])
def api_search_user_view(request):

    if request.method == 'PUT':        
        response_data = {}

        query = request.data.get("query", None)
        if query is None:
            response_data["message"] = "Erro - No Query!"
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)


        # searching query in user "firstname + lastname + username":
        res = User.objects.annotate(
            combined_name=Concat(
                F('first_name'), Value(' '), F('last_name'), Value(' '), F('username'), 
                output_field=CharField()
            )
        ).annotate(
            rank=SearchRank(SearchVector('combined_name'), SearchQuery(query)),
        ).filter(rank__gt=0.0)

        res = sorted(res, key=lambda u: u.rank * (1 + log2(1 + u.rating)), reverse=True)
        scores = {u.pk: u.rank * (1 + log2(1 + u.rating)) for u in res}
        if res != []:
            max_score = scores[res[0].pk]
            scores = {u: scores[u] / max_score for u in scores}


        scores = {x: 0.0 for x in scores}
        
        scores = [User.objects.get(pk=u_pk) for u_pk in sorted(list(scores.keys()), key=lambda upk: scores[upk], reverse=True)]
        serializer = UserResultSerializer(scores, many=True)

        return Response(data={"result": serializer.data}, status=status.HTTP_200_OK)

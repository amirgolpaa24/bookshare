from rest_framework import serializers

from sharing.models import BookExchange
from account.models import User


class BookExchangeRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookExchange
        fields = [  'book', 'borrower',  ]


class BookExchangeBorrowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookExchange
        fields = [  'request_message', 'request_phone_number',  ]


class UserBorrowListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'borrow_list_to_show', ]


class UserLendListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'lend_list_to_show', ]


class BookRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return {
            'title': obj.title,
            'description': obj.description,
            'page_num': obj.page_num,
            'edition': obj.edition,
            'publisher': obj.publisher,
            'pub_year': obj.pub_year,
            'categories_list': obj.categories_list,
            'authors_list': obj.authors_list,
            'owner_name': obj.owner_name,
            'when_added': obj.when_added,
            'slug': obj.slug,
        }


class UserRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return {
            'first_name': obj.first_name,
            'last_name': obj.last_name,
            'username': obj.username,
            'email': obj.email,
            'rating': obj.rating,
        }


class BorrowRequestPropertiesSerializer(serializers.ModelSerializer):
    book = BookRelatedField(read_only=True)
    borrower = UserRelatedField(read_only=True)
    lender = UserRelatedField(read_only=True)
    
    class Meta:
        model = BookExchange
        fields = [  'book', 'borrower', 'lender', 
                    'slug', 'state', 
                    'when_requested', 'when_ended', 
                    'request_message', 'request_phone_number',  ]


class BorrowedBookPropertiesSerializer(serializers.ModelSerializer):
    book = BookRelatedField(read_only=True)
    borrower = UserRelatedField(read_only=True)
    lender = UserRelatedField(read_only=True)
    
    class Meta:
        model = BookExchange
        fields = [  'book', 'borrower', 'lender', 
                    'slug', 
                    'when_requested', 'when_started',
                    'request_message', 'request_phone_number',  
                    'response_message', 'response_meeting_address', 'response_meeting_time',  ]




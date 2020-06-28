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
            'rating': obj.rating,
            'num_rates': obj.num_rates,
            'num_borrowers': obj.num_borrowers,
        }


class UserRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return {
            'first_name': obj.first_name,
            'last_name': obj.last_name,
            'username': obj.username,
            'email': obj.email,
            'rating': obj.rating,
            'num_rates': obj.num_rates,
            'num_borrowers': obj.num_borrowers,
            'num_lenders': obj.num_lenders
        }


class ExchangePropertiesSerializer(serializers.ModelSerializer):
    book = BookRelatedField(read_only=True)
    borrower = UserRelatedField(read_only=True)
    lender = UserRelatedField(read_only=True)
    
    response_meeting_time = serializers.ReadOnlyField()
    return_meeting_time = serializers.ReadOnlyField()
    book_comment = serializers.ReadOnlyField()
    when_requested = serializers.ReadOnlyField()
    when_started = serializers.ReadOnlyField()
    when_rejected = serializers.ReadOnlyField()
    when_delivered = serializers.ReadOnlyField()
    when_ended = serializers.ReadOnlyField()
    when_closed = serializers.ReadOnlyField()
    when_last_changed = serializers.ReadOnlyField()

    class Meta:
        model = BookExchange
        fields = '__all__'


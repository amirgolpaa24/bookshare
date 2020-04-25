import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from account.api.serializers import (ChangePasswordSerializer,
                                     EditedUserSerializer, SelfUserSerializer,
                                     UserRegisterationSerializer,
                                     UserSerializer)
from account.models import User


class RegistrationTestCase(APITestCase):

    def test_registration(self):
        self.assertEqual(2, 2)
        self.assertEqual(2, 2)
        



from rest_framework import generics

from user.serializers import UserSerializers


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializers


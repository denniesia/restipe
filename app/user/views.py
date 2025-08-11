from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken 
from rest_framework.settings import api_settings

from user.serializers import UserSerializers, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializers

class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    rendered_classes = api_settings.DEFAULT_RENDERER_CLASSES 


from user.serializers import UserSerializer, AuthTokenSerializer

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework import authentication, permissions


class CreateUserView(CreateAPIView):
    """View for creating new user."""

    serializer_class = UserSerializer


class CreateAuthTokenView(ObtainAuthToken):
    """View for creating authentication token for users."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class UserProfileView(RetrieveUpdateAPIView):
    """View for get or updating pofile"""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

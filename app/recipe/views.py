from rest_framework import viewsets

from recipe.serializers import RecipeSerializer
from core.models import Recipe

from rest_framework import authentication, permissions


class RecipeViewSet(viewsets.ModelViewSet):
    """View for using recipe APIs."""
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by("-id")

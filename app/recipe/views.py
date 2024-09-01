from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    RecipeImageSerializer,
    TagSerializer,
    IngredientSerializer
)
from core.models import Recipe, Tag, Ingredient

from rest_framework import (
    authentication,
    permissions,
    status,
    viewsets,
    mixins,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma seperated list of ids to filter.",
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="Comma seperated list of ids to filter",
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """Managing Recipes in database."""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_id_list(self, qs):
        return [int(id_str) for id_str in qs.split(",")]

    def get_queryset(self):
        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset

        if tags:
            tags_id_list = self.get_id_list(tags)
            queryset = queryset.filter(tags__id__in=tags_id_list)

        if ingredients:
            ingredients_id_list = self.get_id_list(ingredients)
            queryset = queryset.filter(
                ingredients__id__in=ingredients_id_list
            )

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT, enum=[0, 1],
                description="Filter by items assigend by recipe.",
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for recipe attribute."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assigned_only = bool(
            int(self.request.query_params.get("assigned_only", "0"))
        )
        queryset = self.queryset

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by("-name").distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """Managing tags in database."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in database."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()

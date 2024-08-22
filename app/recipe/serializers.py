from rest_framework.serializers import ModelSerializer

from core.models import Recipe


class RecipeSerializer(ModelSerializer):
    """Serializer for recipe model preview."""

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_to_get_ready", "price", "link"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe model details."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]

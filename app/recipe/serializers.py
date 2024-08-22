from rest_framework.serializers import ModelSerializer

from core.models import Recipe


class RecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_to_get_ready", "price", "link"]
        read_only_fields = ["id"]

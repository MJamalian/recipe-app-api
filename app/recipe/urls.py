from django.urls import path, include
from rest_framework import routers

from recipe import views


router = routers.DefaultRouter()
router.register("recipes", views.RecipeViewSet)
router.register("tags", views.TagViewSet)
router.register("ingredients", views.IngredientViewSet)

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls))
]

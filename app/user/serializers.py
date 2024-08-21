from rest_framework import serializers
from django.contrib.auth import (
    get_user_model, authenticate
)
from django.utils.translation import gettext as _


class UserSerializer(serializers.ModelSerializer):
    """Class for serializing user model."""

    class Meta:
        model = get_user_model()
        fields = ["email", "name", "password"]
        extra_kwargs = {"password": {"min_length": 5, "write_only": True}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Class for serializing authentication tokens."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            msg = _("Unable to authenticate using this credential.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs

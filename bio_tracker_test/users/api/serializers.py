import redis
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers

from bio_tracker_test.users.models import User as UserType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    class Meta:
        model = User
        fields = ["name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


# Artem's code via https://stackoverflow.com/questions/64498554/how-to-add-custom-user-fields-of-dj-rest-auth-package
class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ("name",)


class CustomLoginSerializer(LoginSerializer):
    otp = serializers.IntegerField(required=True)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        otp = attrs.get("otp")

        # check pin

        r = redis.StrictRedis(host="redis", port=6379, decode_responses=True)

        if not r.exists(email):
            msg = _("Unable to log in, smth wrong with otp (expire or not exist).")
            raise exceptions.ValidationError(msg)

        pin = r.get(email)

        if not (pin == str(otp)):
            msg = _("Unable to log in with provided otp.")
            raise exceptions.ValidationError(msg)

        user = self.get_auth_user(username, email, password)

        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise exceptions.ValidationError(msg)

        # Did we get back an active user?
        self.validate_auth_user_status(user)

        # If required, is the email verified?
        if "dj_rest_auth.registration" in settings.INSTALLED_APPS:
            self.validate_email_verification_status(user, email=email)

        attrs["user"] = user
        return attrs

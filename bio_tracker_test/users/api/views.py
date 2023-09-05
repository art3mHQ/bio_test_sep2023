import random

import redis
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from bio_tracker_test.users.tasks import send_feedback_email_task, send_otp_task

from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


# Artem


class DeleteAccount(APIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    # print("ggg_from_ggg")

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        name_to_send_to_celery = str(user.email)

        # send task to celery
        send_feedback_email_task.delay(name_to_send_to_celery)

        user.delete()

        return Response({"result": "user deleted"})


class MakeSaveSendOtp(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        email = self.request.data["email_address"]

        r = redis.StrictRedis(host="redis", port=6379, decode_responses=True)

        otp_code = random.randrange(100000, 999999)

        # create pin
        r.set(email, otp_code)
        r.expire(email, 600)  # 1800 seconds = 1/2 hour

        # send task to celery
        send_otp_task.delay(email, otp_code)

        return Response({"result": "OTP must be send, check email"})

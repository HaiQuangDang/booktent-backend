from django.contrib.auth.models import User
from rest_framework import generics, permissions
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny



class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class DeleteUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny] 
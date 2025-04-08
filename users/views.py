from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdminUser
from django.core.exceptions import PermissionDenied
from backend.admin_views import StandardResultsSetPagination


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  
    def get_serializer_context(self):
        return {"request": self.request}  # Pass request context


class DeleteUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # Any authenticated user can access

    def perform_destroy(self, instance):
        # If the user is deleting themselves, allow it
        if instance == self.request.user:
            instance.delete()
            return
        
        # Superusers cannot delete themselves or other superusers
        if instance.is_superuser:
            raise PermissionDenied("Superusers cannot be deleted.")
        
        # Staff (Admins) can delete regular users
        if self.request.user.is_staff:
            instance.delete()
            return

        raise PermissionDenied("You do not have permission to delete this user.")



class AdminCheckView(APIView):
    permission_classes = [IsAuthenticated]  # Only logged-in users can access
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser
        })


class ListUsersView(generics.ListAPIView):  # Only admins can access
    queryset = User.objects.all().order_by('-date_joined')  # optional: sort newest first
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)
    

class UpdateUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user  # Users can only update their own profile
    
    def get_serializer_context(self):
        return {"request": self.request}  # Pass request context

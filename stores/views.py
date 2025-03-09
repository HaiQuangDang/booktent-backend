from django.shortcuts import render
# Create your views here.
from rest_framework import generics, permissions, serializers
from .models import Store
from .serializers import StoreSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

class StoreListCreateView(generics.ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if Store.objects.filter(owner=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You already have a store."})
        serializer.save(owner=self.request.user)  # Set the store owner to the logged-in user

class StoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        store = self.get_object()
        if self.request.user == store.owner or self.request.user.is_staff:
            serializer.save()
        else:
            raise permissions.PermissionDenied("You do not have permission to update this store.")

    def perform_destroy(self, instance):
        if self.request.user == instance.owner or self.request.user.is_staff:
            instance.delete()
        else:
            raise permissions.PermissionDenied("You do not have permission to delete this store.")

class MyStoreView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the store owned by the authenticated user"""
        try:
            store = Store.objects.get(owner=request.user)
            return Response(StoreSerializer(store).data)
        except Store.DoesNotExist:
            # return Response({"detail": "No store found"}, status=404)
            return Response({"detail": "No store found"})
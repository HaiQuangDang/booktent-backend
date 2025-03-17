from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer
from books.models import Book

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get the current user's cart."""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def add_to_cart(self, request):
        """Add a book to the cart or update quantity."""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        book_id = request.data.get("book_id")
        quantity = int(request.data.get("quantity", 1))

        if not book_id:
            return Response({"error": "Book ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, book=book,
            defaults={"price": book.price, "store": book.store}
        )

        if not created:
            cart_item.quantity += quantity  # If already exists, update quantity

        cart_item.price = book.price  # Ensure price stays correct
        cart_item.store = book.store
        cart_item.save()

        return Response(CartSerializer(cart).data)

    def update_quantity(self, request, pk=None):
        """Update the quantity of a cart item."""
        try:
            cart_item = CartItem.objects.get(id=pk, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get("quantity", 1))
        if quantity <= 0:
            cart_item.delete()  # Remove item if quantity is 0
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return Response(CartSerializer(cart_item.cart).data)

    def remove_from_cart(self, request, pk=None):
        """Remove an item from the cart."""
        try:
            cart_item = CartItem.objects.get(id=pk, cart__user=request.user)
            cart = cart_item.cart
            cart_item.delete()
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    def clear_cart(self, request):
        """Clear all items from the cart."""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)
    
    def check(self, request, pk=None):
        """Check if a book is in the user's cart"""
        try:
            cart = Cart.objects.get(user=request.user)
            exists = CartItem.objects.filter(cart=cart, book_id=pk).exists()
            return Response({"exists": exists}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"exists": False}, status=status.HTTP_200_OK)
